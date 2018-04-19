"""Static User Configuration models"""
import configparser

from onelogin_aws_cli.userquery import user_choice


class ConfigurationFile(configparser.ConfigParser):
    """Represents a configuration ini file on disk"""

    DEFAULTS = dict(save_password=False)

    def __init__(self, config_file=None):
        super().__init__(default_section='defaults')

        self[self.default_section] = dict(self.DEFAULTS)

        self.file = config_file

        if self.file is not None:
            self.load()

    @property
    def has_defaults(self) -> bool:
        """True if the defaults section has settings beyond our defaults"""
        return len(self.defaults()) > len(self.DEFAULTS)

    @property
    def is_initialised(self) -> bool:
        """True if there is at least one section or a defaults section"""
        return len(
            self.sections()
        ) > 0 or self.has_defaults

    def load(self):
        self.read_file(self.file)
        # For backwards compatibility, we check if they have a default
        # section instead of a defaults section and do a little switcheroo as
        # needed.
        if self.has_section('default') and not self.has_defaults:
            print("It looks like you're using a the deprecated 'default' "
                  "section.\nConsider renaming the section to 'defaults'.")
            self.default_section = 'default'

    def initialise(self, config_name=None):
        """
        Prompt the user for configurations, and save them to the
        onelogin-aws-cli config file
        """
        print("Configure Onelogin and AWS\n\n")
        if not config_name:
            config_name = self.default_section

        config_section = self.section(config_name)

        config_section['base_uri'] = user_choice(
            "Pick a Onelogin API server:", [
                "https://api.us.onelogin.com/",
                "https://api.eu.onelogin.com/"
            ]
        )

        print("\nOnelogin API credentials. These can be found at:\n"
              "https://admin.us.onelogin.com/api_credentials")
        config_section['client_id'] = input("Onelogin API Client ID: ")
        config_section['client_secret'] = input("Onelogin API Client Secret: ")
        print("\nOnelogin AWS App ID. This can be found at:\n"
              "https://admin.us.onelogin.com/apps")
        config_section['aws_app_id'] = input("Onelogin App ID for AWS: ")
        print("\nOnelogin subdomain is 'company' for login domain of "
              "'comany.onelogin.com'")
        config_section['subdomain'] = input("Onelogin subdomain: ")

        self.save()

    def save(self):
        """Save this config to disk"""
        self.write(self.file)
        print("Configuration written to '{}'".format(self.file))

    def section(self, section_name: str):
        """
        Return a Section object representing a single section within the
        onelogin config file.

        :param section_name: Name of the section in the config file
        :return:
        """
        if not section_name:
            section_name = self.default_section
        if section_name != self.default_section and \
                not self.has_section(section_name):
            self.add_section(section_name)
        return Section(section_name, self)


class Section(object):
    """Represents a single section in an ini file"""

    def __init__(self, section_name: str, config: ConfigurationFile):
        self.config = config
        self.section_name = section_name
        self._overrides = {}

    @property
    def can_save_password(self) -> bool:
        """
        If the user has specified that the password can be saved to the system
        keychain
        :return:
        """
        return self.config.getboolean(self.section_name, "save_password")

    def set_overrides(self, overrides: dict):
        """
        Specify a dictionary values which take precedence over the existing
        values, but will not overwrite them in the config file.
        :param overrides:
        """
        self._overrides = overrides

    def __setitem__(self, key, value):
        self.config.set(self.section_name, key, value)

    def __getitem__(self, item):
        if item in self._overrides:
            return self._overrides[item]
        return self.config.get(self.section_name, item)

    def __contains__(self, item):
        return self.config.has_option(self.section_name, item)
