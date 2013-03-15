'''
Created on Mar 14, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides caching support.
'''

import weakref

# --------------------------------------------------------------------

class Key:
    '''
    The cache key.
    '''
    __slots__ = ('_has', '_value')
    
    def __init__(self):
        '''
        Construct the key.
        '''
        self._has = False
    
    def set(self, value):
        '''
        Set the value for the key.
        
        @param value: object
            The value to set for the key.
        '''
        self._value = value
        self._has = True
        
    has = property(lambda self: self._has, doc='''
    @rtype: boolean
    Checks if there is any value on this key.
    ''')
    value = property(lambda self: self._value, set, doc='''
    @rtype: object
    Get or Set the value of the key.
    ''')
    
# --------------------------------------------------------------------

class CacheWeak:
    '''
    Container for cache objects based on keys with weak reference.
    '''
    __slots__ = ('_cache', '_interval', '_count')
    
    def __init__(self, interval=10):
        '''
        Construct the weak cache.
        
        @param interval: integer
            The additions interval to check for expired keys.
        '''
        assert isinstance(interval, int), 'Invalid interval %s' % interval
        assert interval > 0, 'A value greater then 0 is required, got %s' % interval
        
        self._cache = {}
        self._interval = interval
        self._count = 0
        
    def key(self, *keys):
        '''
        Provides the key where to place the cached value.
        
        @param keys: arguments[objects]
            The keys to construct the weak key based on.
        @return: Key
            The cached key that holds the value.
        '''
        assert keys, 'At least one key is required'
        keyRef, valid = [], False
        for key in keys:
            if key is None or isinstance(key, str):
                keyRef.append((False, key))
            else:
                keyRef.append((True, weakref.ref(key)))
                valid = True
        if not valid: raise TypeError('No key from [%s] can have a weak reference' % ', '.join(str(key) for key in keys))
        keyRef = tuple(keyRef)
        
        key = self._cache.get(keyRef)
        if key is None:
            if self._count % self._interval == 0: self.cleanup()
            self._count += 1
            key = self._cache[keyRef] = Key()
        
        return key
    
    def cleanup(self):
        '''
        Cleans the cache of the expired keys.
        '''
        expired = []
        for key in self._cache:
            for isWeak, value in key:
                if isWeak and value() is None:
                    expired.append(key)
                    break
        for key in expired: self._cache.pop(key)
