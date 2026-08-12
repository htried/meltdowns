/*
 * libnoisy.c - LD_PRELOAD library for probabilistic network failures
 * 
 * Intercepts getaddrinfo() and connect() calls to simulate DNS and connection-level failures.
 * HTTP/HTTPS error injection (404, 403) is handled by mitmproxy.
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <time.h>
#include <netinet/in.h>

typedef enum {
    ERROR_MODE_NONE = 0,
    ERROR_MODE_DNS_FAILURE = 1,
    ERROR_MODE_CONNECTION_REFUSED = 2
} error_mode_t;

// Configuration from environment
static double failure_rate = 0.0;
static char **blocked_domains = NULL;
static int num_blocked = 0;
static char **allowed_domains = NULL;
static int num_allowed = 0;
// Cache resolved IPs (numeric strings) for blocked domains to check in connect()
static char **blocked_ips = NULL;
static char **blocked_ip_domains = NULL; // Maps each IP to its domain
static int num_blocked_ips = 0;
// Cache resolved IPs for allowed domains (egress allowlist connect checks)
static char **allowed_ips = NULL;
static int num_allowed_ips = 0;
static int debug = 0;
static int initialized = 0;
static error_mode_t error_mode = ERROR_MODE_NONE;
static int error_mode_initialized = 0;
// EGRESS_MODE: 0=open, 1=allowlist, 2=lockdown
#define EGRESS_OPEN 0
#define EGRESS_ALLOWLIST 1
#define EGRESS_LOCKDOWN 2
static int egress_mode = EGRESS_OPEN;

static int (*original_getaddrinfo)(const char *node, const char *service,
                                   const struct addrinfo *hints,
                                   struct addrinfo **res) = NULL;
static int (*original_connect)(int sockfd, const struct sockaddr *addr,
                               socklen_t addrlen) = NULL;
static int (*original_execve)(const char *pathname, char *const argv[],
                              char *const envp[]) = NULL;

static char **blocked_commands = NULL;
static int num_blocked_commands = 0;
static int command_error_mode = -1; // -1=None (just delay), 0=ENOENT, 1=EACCES
static double command_delay = 0.0;
static double command_failure_rate = 1.0;

static void init_error_mode(void);
static const char* get_error_mode_name(error_mode_t mode);
static int should_apply_error(void);
static int apply_dns_error(void);
static int apply_connection_error(void);
static int should_target_domain(const char *hostname);
static void cache_ips_for_domain(const char *domain, const struct addrinfo *res);
static void cache_allowed_ips_for_domain(const char *domain, const struct addrinfo *res);
static int is_allowed_addr(const struct sockaddr *addr, socklen_t addrlen);
static int egress_hostname_allowed(const char *hostname);

static int has_domain_suffix(const char *domain, const char *suffix) {
    size_t dlen, slen;
    if (!domain || !suffix) return 0;
    dlen = strlen(domain);
    slen = strlen(suffix);
    if (dlen < slen) return 0;
    if (strcmp(domain, suffix) == 0) return 1;
    if (dlen > slen && domain[dlen - slen - 1] == '.' &&
        strcmp(domain + (dlen - slen), suffix) == 0) {
        return 1;
    }
    return 0;
}

static void parse_domain_list(const char *domains_str, char ***out_domains, int *out_count) {
    char *domains_copy, *token;
    int count = 0;
    int i = 0;

    *out_domains = NULL;
    *out_count = 0;
    if (!domains_str || !*domains_str) return;

    domains_copy = strdup(domains_str);
    token = strtok(domains_copy, ",");
    while (token) {
        count++;
        token = strtok(NULL, ",");
    }
    free(domains_copy);

    if (count <= 0) return;

    *out_domains = malloc((count + 1) * sizeof(char *));
    domains_copy = strdup(domains_str);
    token = strtok(domains_copy, ",");
    while (token) {
        while (*token == ' ') token++;
        char *end = token + strlen(token) - 1;
        while (end > token && *end == ' ') end--;
        *(end + 1) = '\0';
        (*out_domains)[i++] = strdup(token);
        token = strtok(NULL, ",");
    }
    (*out_domains)[i] = NULL;
    *out_count = i;
    free(domains_copy);
}

static void init_config() {
    if (initialized) return;
    
    char *rate_str = getenv("NETWORK_FAILURE_RATE");
    if (rate_str) {
        failure_rate = atof(rate_str);
    }
    
    parse_domain_list(getenv("BLOCKED_DOMAINS"), &blocked_domains, &num_blocked);
    parse_domain_list(getenv("ALLOWED_DOMAINS"), &allowed_domains, &num_allowed);

    {
        const char *egress = getenv("EGRESS_MODE");
        egress_mode = EGRESS_OPEN;
        if (egress) {
            if (strcmp(egress, "allowlist") == 0 || strcmp(egress, "allow") == 0) {
                egress_mode = EGRESS_ALLOWLIST;
            } else if (strcmp(egress, "lockdown") == 0 ||
                       strcmp(egress, "locked") == 0 ||
                       strcmp(egress, "none") == 0) {
                egress_mode = EGRESS_LOCKDOWN;
            } else if (strcmp(egress, "open") == 0 || strcmp(egress, "full") == 0) {
                egress_mode = EGRESS_OPEN;
            }
        }
    }
    
    debug = getenv("NOISY_DEBUG") != NULL;
    
    // Resolve explicit blocked domains up-front for connect() matching.
    original_getaddrinfo = dlsym(RTLD_NEXT, "getaddrinfo");
    if (blocked_domains && original_getaddrinfo) {
        blocked_ips = malloc(1024 * sizeof(char*));
        blocked_ip_domains = malloc(1024 * sizeof(char*));
        num_blocked_ips = 0;
        for (int i = 0; i < num_blocked; i++) {
            struct addrinfo hints = {0};
            hints.ai_socktype = SOCK_STREAM;
            hints.ai_family = AF_UNSPEC;
            struct addrinfo *res = NULL;
            if (original_getaddrinfo(blocked_domains[i], NULL, &hints, &res) == 0 && res) {
                for (struct addrinfo *ai = res; ai != NULL; ai = ai->ai_next) {
                    char host[NI_MAXHOST];
                    if (getnameinfo(ai->ai_addr, ai->ai_addrlen, host, sizeof(host), NULL, 0, NI_NUMERICHOST) == 0) {
                        if (num_blocked_ips < 1024) {
                            blocked_ips[num_blocked_ips] = strdup(host);
                            blocked_ip_domains[num_blocked_ips] = strdup(blocked_domains[i]);
                            num_blocked_ips++;
                        }
                    }
                }
                freeaddrinfo(res);
            }
        }
        if (debug) {
            fprintf(stderr, "[libnoisy] Cached %d blocked IPs for %d domains\n", num_blocked_ips, num_blocked);
        }
    }

    // Resolve allowlisted domains for EGRESS_MODE=allowlist connect() checks.
    if (egress_mode == EGRESS_ALLOWLIST && allowed_domains && original_getaddrinfo) {
        allowed_ips = malloc(1024 * sizeof(char*));
        num_allowed_ips = 0;
        for (int i = 0; i < num_allowed; i++) {
            struct addrinfo hints = {0};
            hints.ai_socktype = SOCK_STREAM;
            hints.ai_family = AF_UNSPEC;
            struct addrinfo *res = NULL;
            if (original_getaddrinfo(allowed_domains[i], NULL, &hints, &res) == 0 && res) {
                cache_allowed_ips_for_domain(allowed_domains[i], res);
                freeaddrinfo(res);
            }
        }
        if (debug) {
            fprintf(stderr, "[libnoisy] Cached %d allowed IPs for egress allowlist (%d domains)\n",
                    num_allowed_ips, num_allowed);
        }
    }
    
    // Initialize error mode
    init_error_mode();

    parse_domain_list(getenv("NOISY_BLOCKED_COMMANDS"), &blocked_commands, &num_blocked_commands);
    
    char *cmd_mode_str = getenv("NOISY_COMMAND_ERROR_MODE");
    if (cmd_mode_str) {
        if (strcmp(cmd_mode_str, "eacces") == 0 || strcmp(cmd_mode_str, "eaccess") == 0 || strcmp(cmd_mode_str, "1") == 0) {
            command_error_mode = 1;
        } else if (strcmp(cmd_mode_str, "enoent") == 0 || strcmp(cmd_mode_str, "0") == 0) {
            command_error_mode = 0;
        } else {
            command_error_mode = -1;
        }
    } else {
        command_error_mode = -1;
    }
    
    char *cmd_delay_str = getenv("NOISY_COMMAND_DELAY");
    if (cmd_delay_str) {
        command_delay = atof(cmd_delay_str);
    }
    
    char *cmd_rate_str = getenv("NOISY_COMMAND_FAILURE_RATE");
    if (cmd_rate_str) {
        command_failure_rate = atof(cmd_rate_str);
    } else {
        command_failure_rate = 1.0;
    }

    original_execve = dlsym(RTLD_NEXT, "execve");
    
    if (debug) {
        const char *egress_name = "open";
        if (egress_mode == EGRESS_ALLOWLIST) egress_name = "allowlist";
        else if (egress_mode == EGRESS_LOCKDOWN) egress_name = "lockdown";
        fprintf(stderr, "[libnoisy] Initialized: rate=%.2f, blocked=%d domains, allowed=%d domains, egress=%s, error_mode=%s, blocked_cmds=%d\n",
                failure_rate, num_blocked, num_allowed,
                egress_name,
                get_error_mode_name(error_mode), num_blocked_commands);
    }
    
    initialized = 1;
}

// Check if a hostname is in the blocked list
static int is_blocked_domain(const char *hostname) {
    if (!hostname || !blocked_domains) return 0;
    
    for (int i = 0; i < num_blocked; i++) {
        if (has_domain_suffix(hostname, blocked_domains[i])) {
            return 1;
        }
    }
    return 0;
}

static int is_allowed_domain(const char *hostname) {
    if (!hostname || !allowed_domains) return 0;

    for (int i = 0; i < num_allowed; i++) {
        if (has_domain_suffix(hostname, allowed_domains[i])) {
            return 1;
        }
    }
    return 0;
}

static int egress_hostname_allowed(const char *hostname) {
    if (!hostname) return 0;
    if (strcmp(hostname, "localhost") == 0 ||
        strcmp(hostname, "127.0.0.1") == 0 ||
        strcmp(hostname, "::1") == 0) {
        return 1;
    }
    if (egress_mode == EGRESS_OPEN) return 1;
    if (egress_mode == EGRESS_LOCKDOWN) return 0;
    return is_allowed_domain(hostname);
}

static void cache_allowed_ips_for_domain(const char *domain, const struct addrinfo *res) {
    if (!domain || !res) return;
    if (!allowed_ips) {
        allowed_ips = malloc(1024 * sizeof(char*));
        num_allowed_ips = 0;
    }
    for (const struct addrinfo *ai = res; ai != NULL; ai = ai->ai_next) {
        char host[NI_MAXHOST];
        int seen = 0;
        if (getnameinfo(ai->ai_addr, ai->ai_addrlen, host, sizeof(host), NULL, 0, NI_NUMERICHOST) != 0) {
            continue;
        }
        for (int i = 0; i < num_allowed_ips; i++) {
            if (strcmp(allowed_ips[i], host) == 0) {
                seen = 1;
                break;
            }
        }
        if (!seen && num_allowed_ips < 1024) {
            allowed_ips[num_allowed_ips++] = strdup(host);
        }
    }
}

static int is_allowed_addr(const struct sockaddr *addr, socklen_t addrlen) {
    if (!addr || !allowed_ips || num_allowed_ips == 0) return 0;
    char host[NI_MAXHOST];
    if (getnameinfo(addr, addrlen, host, sizeof(host), NULL, 0, NI_NUMERICHOST) != 0) {
        return 0;
    }
    for (int i = 0; i < num_allowed_ips; i++) {
        if (strcmp(host, allowed_ips[i]) == 0) return 1;
    }
    return 0;
}

static int should_target_domain(const char *hostname) {
    if (!hostname) return 0;
    if (strcmp(hostname, "localhost") == 0 ||
        strcmp(hostname, "127.0.0.1") == 0 ||
        strcmp(hostname, "::1") == 0) {
        return 0;
    }

    if (num_blocked > 0) {
        return is_blocked_domain(hostname);
    }

    return !is_allowed_domain(hostname);
}

static void cache_ips_for_domain(const char *domain, const struct addrinfo *res) {
    if (!domain || !res) return;

    if (!blocked_ips) {
        blocked_ips = malloc(1024 * sizeof(char*));
        blocked_ip_domains = malloc(1024 * sizeof(char*));
        num_blocked_ips = 0;
    }

    for (const struct addrinfo *ai = res; ai != NULL; ai = ai->ai_next) {
        char host[NI_MAXHOST];
        int seen = 0;
        if (getnameinfo(ai->ai_addr, ai->ai_addrlen, host, sizeof(host), NULL, 0, NI_NUMERICHOST) != 0) {
            continue;
        }
        for (int i = 0; i < num_blocked_ips; i++) {
            if (strcmp(blocked_ips[i], host) == 0) {
                seen = 1;
                break;
            }
        }
        if (!seen && num_blocked_ips < 1024) {
            blocked_ips[num_blocked_ips] = strdup(host);
            blocked_ip_domains[num_blocked_ips] = strdup(domain);
            num_blocked_ips++;
        }
    }
}

// Check if an address matches any cached blocked IP
static int is_blocked_addr(const struct sockaddr *addr, socklen_t addrlen) {
    if (!addr || !blocked_ips || num_blocked_ips == 0) return 0;
    char host[NI_MAXHOST];
    if (getnameinfo(addr, addrlen, host, sizeof(host), NULL, 0, NI_NUMERICHOST) != 0) {
        return 0;
    }
    for (int i = 0; i < num_blocked_ips; i++) {
        if (strcmp(host, blocked_ips[i]) == 0) return 1;
    }
    return 0;
}

// Check if an address is localhost
static int is_localhost(const struct sockaddr *addr) {
    if (!addr) return 0;
    
    if (addr->sa_family == AF_INET) {
        struct sockaddr_in *sin = (struct sockaddr_in*)addr;
        return (sin->sin_addr.s_addr == htonl(INADDR_LOOPBACK));
    } else if (addr->sa_family == AF_INET6) {
        struct sockaddr_in6 *sin6 = (struct sockaddr_in6*)addr;
        return IN6_IS_ADDR_LOOPBACK(&sin6->sin6_addr);
    }
    return 0;
}

// Generate random number between 0 and 1
static double random_double() {
    return (double)rand() / RAND_MAX;
}

static error_mode_t parse_error_mode(const char *mode_str) {
    if (!mode_str) return ERROR_MODE_NONE;
    
    if (strcmp(mode_str, "dns_failure") == 0) return ERROR_MODE_DNS_FAILURE;
    if (strcmp(mode_str, "connection_refused") == 0) return ERROR_MODE_CONNECTION_REFUSED;
    
    return ERROR_MODE_NONE;
}

static const char* get_error_mode_name(error_mode_t mode) {
    switch (mode) {
        case ERROR_MODE_NONE: return "none";
        case ERROR_MODE_DNS_FAILURE: return "dns_failure";
        case ERROR_MODE_CONNECTION_REFUSED: return "connection_refused";
        default: return "unknown";
    }
}

static void init_error_mode() {
    if (error_mode_initialized) return;
    
    char *mode_str = getenv("NOISY_ERROR_MODE");
    error_mode = parse_error_mode(mode_str);
    error_mode_initialized = 1;
    
    if (debug) {
        fprintf(stderr, "[libnoisy] Error mode: %s\n", get_error_mode_name(error_mode));
    }
}

static int should_apply_error() {
    if (error_mode == ERROR_MODE_NONE) return 0;
    return random_double() < failure_rate;
}

static int apply_dns_error() {
    return EAI_NONAME;
}

static int apply_connection_error() {
            errno = ECONNREFUSED;
            return -1;
}

int getaddrinfo(const char *node, const char *service,
                const struct addrinfo *hints, struct addrinfo **res) {
    
    init_config();
    
    if (!original_getaddrinfo) {
        original_getaddrinfo = dlsym(RTLD_NEXT, "getaddrinfo");
    }

    if (node && !egress_hostname_allowed(node)) {
        if (debug) {
            fprintf(stderr, "[libnoisy] Egress mode denied DNS for %s\n", node);
        }
        return EAI_NONAME;
    }
    
    int target_domain = (node && should_target_domain(node));

    if (target_domain) {
        if (error_mode == ERROR_MODE_DNS_FAILURE && should_apply_error()) {
            if (debug) {
                fprintf(stderr, "[libnoisy] DNS failure for domain %s\n", node);
            }
            return apply_dns_error();
        }
    }

    int result = original_getaddrinfo(node, service, hints, res);
    if (result == 0 && res && *res && target_domain) {
        cache_ips_for_domain(node, *res);
    }
    if (result == 0 && res && *res && egress_mode == EGRESS_ALLOWLIST && node && is_allowed_domain(node)) {
        cache_allowed_ips_for_domain(node, *res);
    }

    return result;
}

int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    
    init_config();
    
    if (!original_connect) {
        original_connect = dlsym(RTLD_NEXT, "connect");
    }
    
    if (is_localhost(addr)) {
        return original_connect(sockfd, addr, addrlen);
    }

    if (egress_mode == EGRESS_LOCKDOWN) {
        if (debug) {
            fprintf(stderr, "[libnoisy] Egress lockdown denied connect\n");
        }
        errno = ECONNREFUSED;
        return -1;
    }

    if (egress_mode == EGRESS_ALLOWLIST && !is_allowed_addr(addr, addrlen)) {
        if (debug) {
            fprintf(stderr, "[libnoisy] Egress allowlist denied connect\n");
        }
        errno = ECONNREFUSED;
        return -1;
    }
    
    if (is_blocked_addr(addr, addrlen)) {
        if (error_mode == ERROR_MODE_CONNECTION_REFUSED && should_apply_error()) {
            if (debug) {
                fprintf(stderr, "[libnoisy] Connect failure for blocked address\n");
            }
            return apply_connection_error();
        }
    }
    
    return original_connect(sockfd, addr, addrlen);
}

int execve(const char *pathname, char *const argv[], char *const envp[]) {
    init_config();
    
    if (!original_execve) {
        original_execve = dlsym(RTLD_NEXT, "execve");
    }
    
    if (num_blocked_commands > 0 && pathname) {
        const char *bin_name = strrchr(pathname, '/');
        bin_name = bin_name ? bin_name + 1 : pathname;
        
        for (int i = 0; i < num_blocked_commands; i++) {
            if (strcmp(bin_name, blocked_commands[i]) == 0) {
                if (random_double() < command_failure_rate) {
                    if (debug) {
                        fprintf(stderr, "[libnoisy] Intercepted blocked command: %s\n", bin_name);
                    }
                    
                    if (command_delay > 0) {
                        if (debug) {
                            fprintf(stderr, "[libnoisy] Delaying command %s by %.2f seconds\n", bin_name, command_delay);
                        }
                        usleep((useconds_t)(command_delay * 1000000));
                    }
                    
                    if (command_error_mode == 0) {
                        if (debug) {
                            fprintf(stderr, "[libnoisy] Failing command %s with ENOENT\n", bin_name);
                        }
                        errno = ENOENT;
                        return -1;
                    } else if (command_error_mode == 1) {
                        if (debug) {
                            fprintf(stderr, "[libnoisy] Failing command %s with EACCES\n", bin_name);
                        }
                        errno = EACCES;
                        return -1;
                    }
                }
            }
        }
    }
    
    return original_execve(pathname, argv, envp);
}

__attribute__((constructor))
static void init_random() {
    srand(time(NULL) ^ getpid());
}

