# https://www.geeksforgeeks.org/bloom-filters-introduction-and-python-implementation/
# https://github.com/remram44/python-bloom-filter/blob/904cea7522a18a7bbef66d3c6b2ee23738171e5a/src/bloom_filter2/bloom_filter.py#L528
# The above two links have inspired the structure and code for my bloom filter

import mmh3
from bitarray import bitarray
 
 
class BloomFilter(object):
 
    '''
    Class for Bloom filter, using mmh3 hash function
    '''
    def __init__(self, filter_size=100, hash_count=3):
        '''
        filter_size : int
            No of bits in bloom filter
        hash_count : float
            No. of hashes to be used for the filter
        '''
        # Hashes
        self.seeds = self.getSeeds(hash_count)
        # Filter size
        self.items_size = filter_size

        # Bit array of given size
        self.bit_array = bitarray(self.items_size)
 
        # initialize all bits as 0
        self.bit_array.setall(0)
    
    def setBitArray(self, bits):
        self.items_size = len(bits)
        self.bit_array = bits

    def add(self, item):
        '''
        Add an item in the filter
        '''
        for i in self.seeds:
 
            # create digest for given item.
            # i work as seed to mmh3.hash() function
            # With different seed, digest created is different
            digest = mmh3.hash(str(item), i) % self.items_size
 
            # set the bit True in bit_array
            self.bit_array[digest] = True
 
    def check(self, item):
        '''
        Check for existence of an item in filter
        '''
        for i in self.seeds:
            digest = mmh3.hash(str(item), i) % self.items_size
            if self.bit_array[digest] == False:
 
                # if any of bit is False then,its not present
                # in filter
                # else there is probability that it exist
                return False
        return True

    def union(self, bloom_filter):
        """Compute the set union of two bloom filters"""
        self.bit_array |= bloom_filter.getBloomFilter()

    def intersection(self, bloom_filter):
        """Compute the set intersection of two bloom filters"""
        self.bit_array &= bloom_filter.getBloomFilter()

    def getBloomFilter(self):
        """Returns the bloom filter stored in the object"""
        return self.bit_array

    @classmethod
    def getSeeds(self, num):
        seeds = []
        temp = [76, 15, 250, 149, 876, 334]
        for i in range(num):
            seeds.append(temp[i%6]+i//6)
        return seeds

