from KSPUtils.config_node_utils.named_object import (
    ChildrenDict,
    NamedObject,
    ValueProperty,
)


class Resource(NamedObject):
    type = "RESOURCE"
    amount = ValueProperty(float)
    maxAmount = ValueProperty(float)


class Module(NamedObject):
    type = "MODULE"


class Part(NamedObject):
    type = "PART"
    mass = ValueProperty(float)
    cost = ValueProperty(float)
    title = ValueProperty(str)
    description = ValueProperty(str)
    resources = ChildrenDict(Resource)
    modules = ChildrenDict(Module)
