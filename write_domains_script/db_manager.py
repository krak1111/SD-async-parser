import psycopg2


def writable_method(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        print("Commit")
        self.connection.commit()
        print("Commited")
        return True
    return wrapper

def add_to_insert_str_params(base_string, params_tuple):
    """
    Method for adding string to query INSERT INTO
    Note: in params_list args MUST BE IN ORDER FOR RECORD and only numeric or string type
    """
    insert_str = ''

    for param in params_tuple:
        if isinstance(param, str):
            insert_str += f'$${param}$$, '
        elif isinstance(param, int):
            insert_str += f'{param}, '

    insert_str = insert_str[:-2]  # delete 2 last symbols ", "
    return base_string + '\n  ' + f'({insert_str}),'

class BaseDBManager(object):

    def __init__(self, db_settings):
        self.connection = psycopg2.connect(db_settings)
        self.cur = self.connection.cursor()





class ManagerForDomains(BaseDBManager):
    def __init__(self, db_settings):
        super().__init__(db_settings)
        self.status_for_new = 'not started'

    @writable_method
    def bring_new_scheme_domain_part(self):
        for type_of_domain in ('primary_domains', 'domains', 'subdomains'):
            self.cur.execute(f"""ALTER TABLE {type_of_domain}
                                  ADD COLUMN IF NOT EXISTS status VARCHAR(15),
                                  ADD COLUMN IF NOT EXISTS url VARCHAR(50)""")
            self.cur.execute(f"ALTER TABLE {type_of_domain} ALTER COLUMN url TYPE VARCHAR(100)")
            self.cur.execute(f"UPDATE {type_of_domain} SET status = 'waiting'")
            self.cur.execute(f"ALTER TABLE {type_of_domain} ALTER COLUMN id TYPE INTEGER")
        
        self.cur.execute("ALTER TABLE subdomains ALTER COLUMN domain_id TYPE INTEGER")
        
        self.cur.execute("ALTER TABLE domains ALTER COLUMN primary_id TYPE INTEGER")
        
        self.cur.execute("ALTER TABLE subdomains_journals ALTER COLUMN subdomain_id TYPE INTEGER")

        return True


    def _get_all_existing(self):
        self._existing_primaries = self._get_existing('primary_domains')
        self._existing_domains = self._get_existing('domains')
        self._existing_subdomains = self._get_existing('subdomains')


    def _get_existing(self, type_of_domain):

        self.cur.execute(f"SELECT name FROM {type_of_domain}")

        return [note[0] for note in self.cur]


    def _split_domains(self):
        """
        This method creates 3 dict for each type of domains
        for primary domains:
        self.all_primaries    {'name': 'url'}
        for domains and subdomains
        self.add_(sub)domains    {'name': ('url', 'parrent domain name')}
        """
        self.all_primaries = {}  # dict like {'name': 'url'}
        self.all_domains = {}  # dict like {'name': ('url', 'parrent')}
        self.all_subdomains = {}  # dict like {'name': ('url', 'parrent')}

        for primary in self.domain_dict:  # primary - dict with keys 'name', 'url', 'domains'

            self.all_primaries[primary['name']] = primary['url']

            for domain in primary['domains']:  # domain - dict with keys 'name', 'url', 'domains'
                self.all_domains[domain['name']] = (domain['url'], primary['name'])

                for subdomain in domain['subdomains']:
                    self.all_subdomains[subdomain['name']] = (subdomain['url'], domain['name'])

        return True


    def _write_primaries_to_db(self):
        """
        Method writes new primary domains and update existing with adding url
        """
        query_to_write_new = 'INSERT INTO primary_domains (name, url, status) VALUES'
        
        print(self._existing_primaries)
        for primary in self.all_primaries:
            primary_url = self.all_primaries[primary]

            if primary in self._existing_primaries:
                print(f"Primary {primary} is existing")
                self.cur.execute('UPDATE primary_domains SET url = %s WHERE name = %s', (primary_url, primary,))
            else:
                print(f"Primary {primary} writing")
                query_to_write_new = add_to_insert_str_params(query_to_write_new, (primary, primary_url, self.status_for_new))

        self.cur.execute(query_to_write_new[:-1])

        return True

    def _write_domains_to_db(self):
        """
        Method writes new domains and update existing with adding url
        """
        
        query_to_write_new = 'INSERT INTO domains (name, url, primary_id, status) VALUES'

        for domain in self.all_domains:  #all_domain is dict like {'domain name': ('domain url', 'parrent primary name')}
            domain_url = self.all_domains[domain][0]
            primary_parrent = self.all_domains[domain][1]

            if domain in self._existing_domains:
                self.cur.execute('UPDATE domains SET url = %s WHERE name = %s', (domain_url, domain,))
            else:
                self.cur.execute("SELECT id FROM primary_domains WHERE name = %s", (primary_parrent,))
                parrent_id = self.cur.fetchone()[0]
                tuple_for_write = (domain, domain_url, parrent_id, self.status_for_new)
                query_to_write_new = add_to_insert_str_params(query_to_write_new, tuple_for_write)

        self.cur.execute(query_to_write_new[:-1])
        return True

    def _write_subdomains_to_db(self):
        """
        Method writes new subdomains and update existing with adding url
        """
        query_to_write_new = 'INSERT INTO subdomains (name, url, domain_id, status) VALUES'
        

        for subdomain in self.all_subdomains:  #all_domain is dict like {'domain name': ('domain url', 'parrent primary name')}
            subdomain_url = self.all_subdomains[subdomain][0]
            domain_parrent = self.all_subdomains[subdomain][1]

            if subdomain in self._existing_subdomains:
                self.cur.execute('UPDATE subdomains SET url = %s WHERE name = %s', (subdomain_url, subdomain,))
            else:
                self.cur.execute("SELECT id FROM domains WHERE name = %s", (domain_parrent,))
                parrent_id = self.cur.fetchone()[0]
                tuple_for_write = (subdomain, subdomain_url, parrent_id, self.status_for_new)
                query_to_write_new = add_to_insert_str_params(query_to_write_new, tuple_for_write)

        self.cur.execute(query_to_write_new[:-1])
        return True


    @writable_method
    def write_all_to_db(self, domain_dict):
        """
        Method-manager for write all domains to db
        """
        self._get_all_existing()
        self.domain_dict = domain_dict

        self._split_domains()

        self._write_primaries_to_db()
        self._write_domains_to_db()
        self._write_subdomains_to_db()

    def out_split_domains(self, domain_dict):

        self.domain_dict = domain_dict

        self._split_domains()
        print('ALL PRIMARIES = ', self.all_primaries)
        print('ALL DOMAINS = ', self.all_domains)
        print('ALL SUBDOMAINS = ', self.all_subdomains)