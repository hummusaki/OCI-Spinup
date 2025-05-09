from oci.config import from_file


def main():
    config = from_file()
    compartment_id = config["tenancy"]
    print("Compartment OCID = ", compartment_id)


if __name__ == "__main__":
    main()
