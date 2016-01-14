#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

"""Volume v2 Type action implementations"""

import logging

from cliff import command
from cliff import lister
from cliff import show
import six

from openstackclient.common import parseractions
from openstackclient.common import utils


class CreateVolumeType(show.ShowOne):
    """Create new volume type"""

    log = logging.getLogger(__name__ + ".CreateVolumeType")

    def get_parser(self, prog_name):
        parser = super(CreateVolumeType, self).get_parser(prog_name)
        parser.add_argument(
            "name",
            metavar="<name>",
            help="New volume type name"
        )
        parser.add_argument(
            "--description",
            metavar="<description>",
            help="New volume type description",
        )
        public_group = parser.add_mutually_exclusive_group()
        public_group.add_argument(
            "--public",
            dest="public",
            action="store_true",
            default=False,
            help="Volume type is accessible to the public",
        )
        public_group.add_argument(
            "--private",
            dest="private",
            action="store_true",
            default=False,
            help="Volume type is not accessible to the public",
        )
        parser.add_argument(
            '--property',
            metavar='<key=value>',
            action=parseractions.KeyValueAction,
            help='Property to add for this volume type'
                 '(repeat option to set multiple properties)',
        )
        return parser

    @utils.log_method(log)
    def take_action(self, parsed_args):

        volume_client = self.app.client_manager.volume

        kwargs = {}
        if parsed_args.public:
            kwargs['is_public'] = True
        if parsed_args.private:
            kwargs['is_public'] = False

        volume_type = volume_client.volume_types.create(
            parsed_args.name,
            description=parsed_args.description,
            **kwargs
        )
        volume_type._info.pop('extra_specs')
        if parsed_args.property:
            result = volume_type.set_keys(parsed_args.property)
            volume_type._info.update({'properties': utils.format_dict(result)})

        return zip(*sorted(six.iteritems(volume_type._info)))


class DeleteVolumeType(command.Command):
    """Delete volume type"""

    log = logging.getLogger(__name__ + ".DeleteVolumeType")

    def get_parser(self, prog_name):
        parser = super(DeleteVolumeType, self).get_parser(prog_name)
        parser.add_argument(
            "volume_type",
            metavar="<volume-type>",
            help="Volume type to delete (name or ID)"
        )
        return parser

    def take_action(self, parsed_args):
        self.log.info("take_action: (%s)", parsed_args)
        volume_client = self.app.client_manager.volume
        volume_type = utils.find_resource(
            volume_client.volume_types, parsed_args.volume_type)
        volume_client.volume_types.delete(volume_type.id)
        return


class ListVolumeType(lister.Lister):
    """List volume types"""

    log = logging.getLogger(__name__ + '.ListVolumeType')

    def get_parser(self, prog_name):
        parser = super(ListVolumeType, self).get_parser(prog_name)
        parser.add_argument(
            '--long',
            action='store_true',
            default=False,
            help='List additional fields in output')
        return parser

    @utils.log_method(log)
    def take_action(self, parsed_args):
        if parsed_args.long:
            columns = ['ID', 'Name', 'Description', 'Extra Specs']
            column_headers = ['ID', 'Name', 'Description', 'Properties']
        else:
            columns = ['ID', 'Name']
            column_headers = columns
        data = self.app.client_manager.volume.volume_types.list()
        return (column_headers,
                (utils.get_item_properties(
                    s, columns,
                    formatters={'Extra Specs': utils.format_dict},
                ) for s in data))


class SetVolumeType(command.Command):
    """Set volume type properties"""

    log = logging.getLogger(__name__ + '.SetVolumeType')

    def get_parser(self, prog_name):
        parser = super(SetVolumeType, self).get_parser(prog_name)
        parser.add_argument(
            'volume_type',
            metavar='<volume-type>',
            help='Volume type to modify (name or ID)',
        )
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='Set volume type name',
        )
        parser.add_argument(
            '--description',
            metavar='<name>',
            help='Set volume type description',
        )
        parser.add_argument(
            '--property',
            metavar='<key=value>',
            action=parseractions.KeyValueAction,
            help='Property to add or modify for this volume type '
                 '(repeat option to set multiple properties)',
        )
        return parser

    @utils.log_method(log)
    def take_action(self, parsed_args):
        volume_client = self.app.client_manager.volume
        volume_type = utils.find_resource(
            volume_client.volume_types, parsed_args.volume_type)

        if (not parsed_args.name
                and not parsed_args.description
                and not parsed_args.property):
            self.app.log.error("No changes requested\n")
            return

        kwargs = {}
        if parsed_args.name:
            kwargs['name'] = parsed_args.name
        if parsed_args.description:
            kwargs['description'] = parsed_args.description

        if kwargs:
            volume_client.volume_types.update(
                volume_type.id,
                **kwargs
            )

        if parsed_args.property:
            volume_type.set_keys(parsed_args.property)

        return


class ShowVolumeType(show.ShowOne):
    """Display volume type details"""

    log = logging.getLogger(__name__ + ".ShowVolumeType")

    def get_parser(self, prog_name):
        parser = super(ShowVolumeType, self).get_parser(prog_name)
        parser.add_argument(
            "volume_type",
            metavar="<volume-type>",
            help="Volume type to display (name or ID)"
        )
        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action: (%s)", parsed_args)
        volume_client = self.app.client_manager.volume
        volume_type = utils.find_resource(
            volume_client.volume_types, parsed_args.volume_type)
        properties = utils.format_dict(volume_type._info.pop('extra_specs'))
        volume_type._info.update({'properties': properties})
        return zip(*sorted(six.iteritems(volume_type._info)))


class UnsetVolumeType(command.Command):
    """Unset volume type properties"""

    log = logging.getLogger(__name__ + '.UnsetVolumeType')

    def get_parser(self, prog_name):
        parser = super(UnsetVolumeType, self).get_parser(prog_name)
        parser.add_argument(
            'volume_type',
            metavar='<volume-type>',
            help='Volume type to modify (name or ID)',
        )
        parser.add_argument(
            '--property',
            metavar='<key>',
            default=[],
            required=True,
            help='Property to remove from volume type '
                 '(repeat option to remove multiple properties)',
        )
        return parser

    @utils.log_method(log)
    def take_action(self, parsed_args):
        volume_client = self.app.client_manager.volume
        volume_type = utils.find_resource(
            volume_client.volume_types,
            parsed_args.volume_type,
        )
        volume_type.unset_keys(parsed_args.property)
        return
