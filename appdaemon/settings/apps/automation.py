import appdaemon.plugins.hass.hassapi as hass

class Base(hass.Hass):
    """Define a base automation object."""
    
    def initialize(self) -> None:
        """Initialize."""
        # self.log('Initialize base')

        # Define a holding place for HASS entity IDs:
        self.entity_ids = self.args.get('entity_ids', {})

        # Define a holding place for any scheduler handles that the automation
        # wants to keep track of:
        self.handles = {}  # type: Dict[str, str]

        # Define a holding place for key/value properties for this automation:
        self.properties = self.args.get('properties', {})

        # Take every dependecy and create a reference to it:
        for app in self.args.get('dependencies', []):
            if not getattr(self, app, None):
                setattr(self, app, self.get_app(app))

class Automation(Base):
    """Define a base automation object."""

    def initialize(self) -> None:
        """Initialize."""
        super().initialize()
        # self.log('Initialize automation')
        
        # Define a reference to the "manager app" – for example, a trash-
        # related automation might carry a reference to TrashManager:
        if self.args.get('app'):
            self.app = getattr(self, self.args['app'])

        # Set the entity ID of the input boolean that will control whether
        # this automation is enabled or not:
        self.enabled_entity_id = None  # type: ignore
        enabled_config = self.args.get('enabled_config', {})
        if enabled_config:
            if enabled_config.get('toggle_name'):
                self.enabled_entity_id = 'input_boolean.{0}'.format(
                    enabled_config['toggle_name'])
            else:
                self.enabled_entity_id = 'input_boolean.{0}'.format(self.name)
        
        # Register any "mode alterations" for this automation – for example,
        # perhaps it should be disabled when Vacation Mode is enabled:
        mode_alterations = self.args.get('mode_alterations', {})
        if mode_alterations:
            for mode, value in mode_alterations.items():
                mode_app = getattr(self, mode)
                mode_app.register_enabled_entity(self.enabled_entity_id, value)
