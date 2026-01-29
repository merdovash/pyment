class Foo:
    """ Foo """
    def get_id_and_uuid(self, regl_id=None, uuid=None, pd_type=None) -> tuple[int, str]:
        """
        Foo (id, uuid) Foo id Foo uuid [Foo]

        :param regl_id: (Default value = None)
        :param uuid: (Default value = None)
        :param pd_type: (Default value = None)
        :rtype: tuple[int,str]

        """
        if regl_id and uuid:
            return regl_id, uuid

        elif regl_id and not uuid:
            reg = self._structure.regulation(regl_id)
            if reg:
                return regl_id, reg.UUID()

        elif uuid and not regl_id:
            reg_id = get_regl_id_by_uuid(uuid)
            if reg_id:
                return reg_id, uuid

        return regl_id, uuid
