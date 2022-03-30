from KSPUtils.config_node_utils.named_object import NamedObject

NamedObject.mirror_value("name")


class Part(NamedObject):
    pass


Part.register("PART")
Part.mirror_value("mass", float)
Part.mirror_value("cost", float)
Part.mirror_value("title")
Part.mirror_value("description")
Part.setup_children_dict("resources", "RESOURCE")
Part.setup_children_dict("modules", "MODULE")


class Resource(NamedObject):
    pass


Resource.register("RESOURCE")
Resource.mirror_value("amount", float)
Resource.mirror_value("maxAmount", float)


class Module(NamedObject):
    pass


Module.register("MODULE")
