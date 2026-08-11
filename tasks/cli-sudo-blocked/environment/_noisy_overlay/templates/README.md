# Error Page Templates

This directory uses one generic template per status code:

- `403.html`
- `404.html`
- `503.html`

`mitmproxy_addon.py` resolves template content only by status code. It no longer loads domain-specific template files.

## Usage

1. Edit one or more status files above.
2. Ensure `NOISY_TEMPLATE_DIR` points to this directory (default: `/utils/templates`).
3. Set `NOISY_ERROR_MODE` to `403`, `404`, or `5xx`.

If a template is missing or unreadable, the addon serves a built-in fallback HTML body.

