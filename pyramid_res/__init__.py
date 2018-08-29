import abc
import logging
from abc import abstractmethod
from collections.__init__ import UserDict, OrderedDict
from typing import AnyStr, Type
from pyramid.interfaces import IRequestFactory
from pyramid.request import Request

logger = logging.getLogger(__name__)


class HasRequestMixin:
    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, new):
        self._request = new

class OperationArgumentGetter(metaclass=abc.ABCMeta):
    @abstractmethod
    def get_value(self, arg, request, arg_context):
        pass


class IResourceManagerHelper:
    pass

class ResourceManager:
    """
    ResourceManager class. Provides access to res operations.
    """
    def __init__(self, config=None,
                 title=None,
                 entity_type=None,
                 node_name=None,
                 mapper_info=None):
        """
        Instantiate a new instance of ResourceManager
        :type registration: ResourceRegistration
        :param config: Configurator class
        :param registration: Registration instance
        """

        self._entity_type = entity_type
        self._config = config
        self._ops = []
        self._opsdict = {}
        self._node_name = node_name
        self._title = title
        # this is not suitable for an extension - TODO
        self._mapper_info = mapper_info
        return

    @property
    def mapper_info(self):
        return self._mapper_info

    @mapper_info.setter
    def mapper_info(self, new) -> None:
        self._mapper_info = new

    @property
    def factory_method(self):
        def factory(mgr: ResourceManager,
                    name: AnyStr = None,
                    parent: 'ContainerResource' = None,
                    title: AnyStr = None):
            return Resource(mgr, name, parent, title)

        return factory

    def operation(self, name, view, args, renderer=None) -> None:
        """
        Add operation to res manager.
        :param name:
        :param view:
        :param renderer:
        :return:
        """
        # should there be an implicit argument???
        args[0:0] = self.implicit_args()
        op = ResourceOperation(name, view, args=args, manager=self, renderer=renderer)
        self._ops.append(op)
        self._opsdict[op.name] = op

    def implicit_args(self):
        args = []
        if self._entity_type is not None:
            args.append(OperationArgument(ENTITY_VIEW_ARG_NAME, Type, default=self._entity_type,
                                          label='Entity Type', implicit_arg=True))
        return args

    def add_action(self, config):
        """
        add_action
        :type config: Configurator
        :param config:
        :return:
        """
        op: ResourceOperation

        reg_view = False

        node_name = self._node_name

        my_parent = config.registry.email_mgmt_app.resources
        root = my_parent

        request = config.registry.queryUtility(IRequestFactory, default=Request)({})
        request.registry = config.registry

        #
        # Populate the root resource dictionary with our
        # { node_name, ContainerResource } pair.
        #
        # ContainerResource is the result of the default factory method
        #
        # Our parent is the "email_mgmt_app.resources" in our
        # app registry. That's the root resource!!

        root[node_name] = self.factory_method \
            (self, name=node_name, title=self._title,
             parent=my_parent)

        request.context = root[node_name]
        request.root = config.registry.email_mgmt_app.resources
        request.subpath = ()
        request.traversed = (node_name,)

        #extra = {'inspect': self._inspect}
        extra = {}
        if self.entity_type is not None:
            # this is a predicate!
            # sanity check this!!
            extra['entity_type'] = self.entity_type
            # this is not a predicate, but is predicateD on having
            # an entity type
            extra['mapper_info'] = self.mapper_info

        # config.add_view(view=lambda rs,rr: rs,renderer='json')
        for op in self._ops:
            d = extra.copy()
            d['operation'] = op
            if op.renderer is not None:
                d['renderer'] = op.renderer

            request.view_name = op.name
            # register an entry point for the view
            entry_point_key = get_entry_point_key(request, root[node_name], op.name)
            d['entry_point_key'] = entry_point_key
            #d['decorator'] = view_decorator
            view_kwargs = {'view': op.view,
                           'name': op.name,
                           'node_name': node_name,
                           **d }

            # We are instantiating an EntryPoint here. We need to give it more
            # info.
            entry_point = EntryPoint(entry_point_key,
                                     js=op.entry_point_js(request),
                                     view_kwargs=view_kwargs,
                                     operation=op)
            config.register_entry_point(entry_point)

            logger.debug("Adding view: %s", repr(d))
            # register_entry_point(epstr)
            v = config.add_view(**view_kwargs)

            reg_view = True

        if not reg_view:
            logger.warning("No view registered!")

    @property
    def ops(self) -> dict:
        return self._opsdict

    # @property
    # def inspect(self):
    #     return self._inspect
    #
    # @inspect.setter
    # def inspect(self, new):
    #     self._inspect = new

    @property
    def entity_type(self):
        return self._entity_type

    @property
    def title(self):
        return self._title


class ArgumentGetter(OperationArgumentGetter):
    def get_value(self, arg, request: Request, arg_context):
        return request.params[arg.name]


class SubpathArgumentGetter(OperationArgumentGetter):
    def get_value(self, arg, request, arg_context):
        logger.warning("Getting %s", arg.name)
        val = request.subpath[arg_context.subpath_index]
        arg_context.subpath_index = arg_context.subpath_index + 1
        return val


class OperationArgument:
    """
    An argument to an operation.
    """
    @staticmethod
    def SubpathArgument(name: AnyStr, argtype, optional: bool=False, default=None, label=None, implicit_arg=False):
        """
        "Convenience" method to create a subpath-sourced argument.
        :param name:
        :param argtype:
        :param optional:
        :param default:
        :param label:
        :param implicit_arg:
        :return:
        """
        return OperationArgument(name, argtype, optional=optional, default=default, getter=SubpathArgumentGetter(),
                                 label=label,implicit_arg=implicit_arg)

    def __init__(self, name: AnyStr, argtype, optional: bool=False, default=None, getter=None, has_value=None, label=None, implicit_arg=False) -> None:
        """

        :param name:
        :param argtype:
        :param optional:
        :param default:
        :param getter:
        :param has_value:
        :param label:
        :param implicit_arg:
        """
        self._default = default
        self._name = name
        self._argtype = argtype
        self._optional = optional
        self._getter = getter
        self._has_value = has_value
        if label is None:
            self._label = self._name
        else:
            self._label = label

        self._implicit_arg = implicit_arg

    def __json__(self, request):
        return { 'name': self.name, 'optional': self.optional, 'default': self.default, 'label': self.label }

    def __str__(self):
        return repr(self.__dict__)

    def __repr__(self):
        return str(self)

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, new):
        self._default = new

    @property
    def name(self) -> AnyStr:
        return self._name

    @property
    def argtype(self):
        return self._argtype

    @property
    def optional(self) -> bool:
        return self._optional

    @property
    def label(self) -> AnyStr:
        return self._label

    @property
    def implicit_arg(self) -> bool:
        return self._implicit_arg

    def get_value(self, request, arg_context):
        if self._getter is not None:
            return self._getter.get_value(self, request, arg_context)

    def has_value(self, request, arg_context):
        if self._has_value is not None:
            return self._has_value(self, request, arg_context)
        return None


class ResourceOperation:
    """
    Class encapsulating an operation on a resource
    """
    def entry_point_js(self, request: Request, prefix: AnyStr=""):
        #inspect: Mapper = self._resource_manager.inspect
        ready_stmts = ''
        rel: RelationshipInfo
        for rel in self._resource_manager.mapper_info['relationships']:
            arg = rel['argument']
            logger.debug("rel.argument = %s", repr(arg))



            combined_key = prefix + rel['key']
            select_id = 'select_%s' % combined_key
            button_id = 'button_%s' % combined_key
            collapse_id = 'collapse_%s' % combined_key
            ready_stmts = ready_stmts + render_template(request,
                                                        'templates/entity/button_create_new_js.jinja2',
                                                        {'select_id': select_id,
                                                         'button_id': button_id,
                                                         'collapse_id': collapse_id})
        ready_js = render_template(request,
                                   'scripts/templates/ready.js.jinja2',
                                   {'ready_js_stmts': ready_stmts})
        entry_point_stmts = render_template(request, 'scripts/templates/entry_point_stmts.js.jinja2',
                               {'statements': ''})
        return render_template(request, 'scripts/templates/entry_point_stmts.js.jinja2',
                               { 'ready_js': ready_js,
                                 'entry_point_stmts': entry_point_stmts })


    def __init__(self, name, view, args, manager: 'ResourceManager', renderer=None) -> None:
        """

        :param name: name of the operation - add, view, etc
        :param view: associated view
        :param renderer: associated renderer
        """
        self._renderer = renderer
        self._args = args
        self._view = view
        self._name = name
        self._resource_manager = manager

    def __json__(self, request):
        return { 'name': self.name, 'args': self.args }

    def __str__(self):
        return repr(self.__dict__)

    @property
    def renderer(self):
        return self._renderer

    @property
    def view(self):
        return self._view

    @property
    def name(self):
        return self._name

    @property
    def args(self):
        return self._args

    @property
    def resource_manager(self):
        return self._resource_manager


class Resource:
    """
    Base resource type. Implements functionality common to all resource types.
    """
    def __init__(self,
                 mgr: ResourceManager,
                 name: AnyStr=None,
                 parent: 'ContainerResource'=None,
                 title: AnyStr=None) -> None:
        """

        :param mgr: ResourceManager instance
        :param name: The name as appropriate for a resource key. (confusing)
        :param parent: Parent resources.
        :param title: Defaults to name if not given.
        """
        assert parent is not None or isinstance(self, RootResource)
        self._title = title
        self.__name__ = name
        self.__parent__ = parent
        self._resource_manager = mgr

    def attach(self, parent, name):
        self.__parent__ = parent
        self.__name__ = name

    def __json__(self, request):
        return { 'title': self.title, '__name__': self.__name__,
        'entity_type': self.entity_type,  }

    def __str__(self):
        return "Resource[%s]" % self.entity_type

    def __repr__(self):
        return str(self)

    @property
    def is_container(self) -> bool:
        return False

    @property
    def title(self):
        return self._title

    def path(self):
        return pyramid.threadlocal.get_current_request().resource_path(self)

    def url(self):
        return pyramid.threadlocal.get_current_request().resource_url(self)

    @property
    def entity_type(self):
        return self.resource_manager.entity_type

    @property
    def resource_manager(self):
        return self._resource_manager


class ContainerResource(Resource, UserDict):
    """
    Resource containing sub-resources.
    """
    def __init__(self, dict_init, mgr, *args, **kwargs) -> None:
        # this is the only spot where we call Resource.__init__
        super().__init__(mgr, *args, **kwargs)
        self.data = OrderedDict(dict_init)

    @property
    def is_container(self) -> bool:
        return True

    def __json__(self, request):
        return { 'entity_type': self.entity_type, 'children': self.data }

    def __getitem__(self, key):
        logger.debug("querying ContainerResource for %s", key)
        v = super().__getitem__(key)
        logger.debug("result is %s", v)
        return v


class LeafResource(Resource):
    def __getattr__(self, item):
        raise KeyError


class RootResource(ContainerResource):
    """
    The root resource for the pyramid application. This is not the same as the RootFactory.
    """
    def __init__(self, dict_init, *args, **kwargs) -> None:
        """
        Initializer for a root resource. This is not a singleton class so it should only be instantiated
        once.
        :param dict_init:
        :param args:
        :param kwargs:
        """
        self.__name__ = ''
        self.__parent__ = None
        super().__init__(dict_init, *args, **kwargs)


def includeme(config):

    pass

