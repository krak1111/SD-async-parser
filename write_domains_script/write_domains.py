import json
import os

from db_manager import ManagerForDomains
import DB_SETTINGS as db_set


def get_all_domains_from_file():
    path = os.path.join(os.getcwd(), 'domains.json')

    with open(path) as file:
        all_domains = json.load(file)

    return all_domains

def main():
    manager = ManagerForDomains(db_set.settings)
    manager.bring_new_scheme_domain_part()
    manager.write_all_to_db(get_all_domains_from_file())


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
