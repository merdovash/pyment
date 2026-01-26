class Foo(Bar):
    """Foo"""

    def before_create(self, fltr: sbis.Record):
        if fltr.Get("__STUB__"):
            self._fix_stub_regulation(self._record)
        else:
            self._fix_regulation(self._record, fltr)