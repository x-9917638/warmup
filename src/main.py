import argparse
import json
import sys
from pathlib import Path

CONTACTS_FILE = "contacts.json"


# Rust brainrot
class Result[T]:
    def __init__(self, err: str | None, val: T) -> None:
        self.err = err
        self.val = val

    def unwrap(self) -> T:
        if self.err:
            msg = f"Called unwrap() on Err variant: {self.err}"
            raise TypeError(msg)
        return self.val


class Contact:
    def __init__(
        self,
        name: str,
        email: str | None,
    ) -> None:
        self.name = name
        self.email = email

    @staticmethod
    def try_from(o: object) -> Result:
        if not isinstance(o, dict):
            return Result(
                f"Task does not implement From for objects of class {o.__class__}",  # noqa: E501
                None,
            )
        key: str | None = None
        try:
            name = o["name"]
            email = o["email"]

            return Result(None, Contact(name, email))
        except KeyError:
            return Result(f"Expected key {key} but did not find in {o}", None)
        except Exception as e:  # noqa: BLE001
            return Result(f"Error: {e=}", None)


class TaskEncoder(json.JSONEncoder):
    def default(self, o: object) -> dict[str, str | None]:
        if isinstance(o, Contact):
            return {
                "name": o.name,
                "email": o.email,
            }
        # Let the base class default method raise the TypeError
        return super().default(o)


def read_contacts() -> dict[int, Contact]:
    path = Path(CONTACTS_FILE)
    if not path.exists():
        return {}
    with path.open() as f:
        data = json.load(f)
        out = {}
        for i in data:
            out[int(i)] = Contact.try_from(data[i]).unwrap()
        return out


def write_contacts(tasks: dict[int, Contact]) -> None:
    with Path(CONTACTS_FILE).open("w") as f:
        json.dump(tasks, f, indent=2, cls=TaskEncoder)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contact",
        type=str,
        nargs="?",
        help="Contact to add",
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Optional contact email",
    )
    parser.add_argument(
        "-d",
        "--delete",
        type=int,
        help="Delete a contact by ID",
        metavar="<ID>",
    )
    parser.add_argument(
        "-l",
        "--list",
        help="List all tasks",
        action="store_true",
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def check_id(id: int) -> None:
    if id < 0:
        print(
            f"[ERROR] ID was {id}, but ID must be a positive integer.",
            file=sys.stderr,
        )
        sys.exit(1)


def handle_args(args: argparse.Namespace) -> None:
    # Instead of checking for args.complete, check for None
    # because user could pass 0 for example.
    if args.delete is not None:
        contact_id = args.delete
        check_id(contact_id)

        contacts = read_contacts()
        if contacts.pop(contact_id, None) is None:
            print(f"[WARN] No contact with ID {contact_id}!")
        write_contacts(contacts)

    # Is always bool
    elif args.list:
        contacts = read_contacts()
        for contact in contacts.values():
            print("==== Contact ====")
            print(
                f"Name: {contact.name}, \nEmail: {contact.email}\n",
            )

    elif args.email is not None:
        if args.contact is None:
            print("[ERROR] Email found but no contact given", file=sys.stderr)
            sys.exit(1)
        contacts = read_contacts()
        next_id = 0
        while next_id in contacts:
            next_id += 1
        contacts[next_id] = Contact(args.contact, args.email)
        write_contacts(contacts)

    elif args.contact is not None:
        contacts = read_contacts()
        next_id = 0
        while next_id in contacts:
            next_id += 1
        contacts[next_id] = Contact(args.contact, None)
        write_contacts(contacts)


def main() -> None:
    args = parse_args()

    handle_args(args)


if __name__ == "__main__":
    main()
