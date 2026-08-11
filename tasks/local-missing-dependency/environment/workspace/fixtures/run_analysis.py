"""Roll-up variance check for the March close (reads partitioned DSV under rollups/)."""

from feldspar_io.dsv import read_partitioned


def main() -> None:
    frame = read_partitioned("rollups/latest/")
    print(frame.summary())


if __name__ == "__main__":
    main()
