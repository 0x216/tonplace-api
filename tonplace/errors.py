class TonPlaceError(Exception):
    """Base class for TonPlace errors"""

    @property
    def message(self):
        '''Returns the first argument used to construct this error.'''
        return self.args[0]