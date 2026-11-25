from collections import UserDict
from datetime import date, datetime, timedelta
from functools import wraps


class Field:
    def __init__(self, value):
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        phone_number = str(value).strip()
        if len(phone_number) != 10 or not phone_number.isdigit():
            raise ValueError("Phone number must contain exactly 10 digits")
        self._value = phone_number


class Birthday(Field):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if isinstance(value, datetime):
            self._value = value.date()
            return
        if isinstance(value, date):
            self._value = value
            return

        try:
            self._value = datetime.strptime(str(value).strip(), "%d.%m.%Y").date()
        except ValueError as error:
            raise ValueError("Invalid date format. Use DD.MM.YYYY") from error

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_to_remove = self.find_phone(phone)
        if phone_to_remove is None:
            raise ValueError("Phone number not found")
        self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone, new_phone):
        phone_to_edit = self.find_phone(old_phone)
        if phone_to_edit is None:
            raise ValueError("Phone number not found")
        phone_to_edit.value = new_phone

    def find_phone(self, phone):
        phone_number = str(phone).strip()
        for record_phone in self.phones:
            if record_phone.value == phone_number:
                return record_phone
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(phone.value for phone in self.phones)
        birthday = str(self.birthday) if self.birthday else "not set"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    @staticmethod
    def _normalize_birthday_year(birthday, year):
        try:
            return birthday.replace(year=year)
        except ValueError:
            return birthday.replace(year=year, day=28)

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday_this_year = self._normalize_birthday_year(record.birthday.value, today.year)
            if birthday_this_year < today:
                birthday_this_year = self._normalize_birthday_year(record.birthday.value, today.year + 1)

            days_until_birthday = (birthday_this_year - today).days
            if 0 <= days_until_birthday <= 7:
                congratulation_date = birthday_this_year
                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append(
                    {
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
                    }
                )

        return upcoming_birthdays


def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Enter the argument for the command."
        except ValueError as error:
            return str(error)

    return inner


def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return ""

    command = parts[0].lower()
    return command, *parts[1:]


@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."

    if phone:
        record.add_phone(phone)

    return message


@input_error
def change_contact(args, book):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")

    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")

    if not record.phones:
        return "No phones for this contact."

    return "; ".join(phone.value for phone in record.phones)


@input_error
def show_all(args, book):
    if not book.data:
        return "No contacts saved."

    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")

    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")

    if record.birthday is None:
        return "Birthday not set."

    return str(record.birthday)


@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays."

    return "\n".join(
        f"{item['name']}: {item['congratulation_date']}" for item in upcoming_birthdays
    )


def main():
    book = AddressBook()
    commands = {
        "hello": lambda args: "How can I help you?",
        "add": lambda args: add_contact(args, book),
        "change": lambda args: change_contact(args, book),
        "phone": lambda args: show_phone(args, book),
        "all": lambda args: show_all(args, book),
        "add-birthday": lambda args: add_birthday(args, book),
        "show-birthday": lambda args: show_birthday(args, book),
        "birthdays": lambda args: birthdays(args, book),
    }

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        parsed = parse_input(user_input)
        if not parsed:
            continue

        command, *args = parsed

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        handler = commands.get(command)
        print(handler(args) if handler else "Invalid command.")


if __name__ == "__main__":
    main()
