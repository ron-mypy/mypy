from mtypes import Type, Instance, Any, TupleType, Callable
from nodes import TypeInfo, FuncBase, Var, FuncDef, AccessorNode, Context
from messages import MessageBuilder
from subtypes import map_instance_to_supertype
from expandtype import expand_type_by_instance
from nodes import method_type


Type analyse_member_access(str name, Type typ, Context node, bool is_lvalue,
                          bool is_super, Type tuple_type, MessageBuilder msg,
                          TypeInfo override_info=None):
    """Analyse member access.

    This is a general operation that supports various different variations:
    
      1. lvalue or non-lvalue access (i.e. setter or getter access)
      2. supertype access (when using the super keyword; is_super == True and
         override_info should refer to the supertype)
    """
    if isinstance(typ, Instance):
        # The base object has an instance type.
        itype = (Instance)typ
        
        info = itype.type
        if override_info:
            info = override_info
        
        # Look up the member. First look up the method dictionary.
        FuncBase method = None
        if not is_lvalue:
            method = info.get_method(name)
        
        if method:
            # Found a method. The call below has a unique result for all valid
            # programs.
            itype = map_instance_to_supertype(itype, method.info)
            return expand_type_by_instance(method_type(method), itype)
        else:
            # Not a method.
            return analyse_member_var_access(name, itype, info, node,
                                             is_lvalue, is_super, msg)
    elif isinstance(typ, Any):
        # The base object has dynamic type.
        return Any()
    elif isinstance(typ, TupleType):
        # Actually look up from the tuple type.
        return analyse_member_access(name, tuple_type, node, is_lvalue,
                                     is_super, tuple_type, msg)
    elif isinstance(typ, Callable) and ((Callable)typ).is_type_obj():
        # Class attribute access.
        return msg.not_implemented('class attributes', node)
    else:
        # The base object has an unsupported type.
        return msg.has_no_member(typ, name, node)


Type analyse_member_var_access(str name, Instance itype, TypeInfo info,
                              Context node, bool is_lvalue, bool is_super,
                              MessageBuilder msg):
    """Analyse member access that does not target a method.

    This is logically part of analyse_member_access and the arguments are
    similar.
    """
    # It was not a method. Try looking up a variable.
    v = lookup_member_var_or_accessor(info, name, is_lvalue)
    
    if isinstance(v, Var):
        # Found a member variable.
        var = (Var)v
        itype = map_instance_to_supertype(itype, var.info)
        # FIX what if more than one?
        if var.type:
            return expand_type_by_instance(var.type, itype)
        else:
            # Implicit dynamic type.
            return Any()
    elif isinstance(v, FuncDef):
        # Found a getter or a setter.
        raise NotImplementedError()
    
    # Could not find the member.
    if is_super:
        msg.undefined_in_superclass(name, node)
        return Any()
    else:
        return msg.has_no_member(itype, name, node)


AccessorNode lookup_member_var_or_accessor(TypeInfo info, str name,
                                           bool is_lvalue):
    """Find the attribute/accessor node that refers to a member of a type."""
    if is_lvalue:
        return info.get_var_or_setter(name)
    else:
        return info.get_var_or_getter(name)
