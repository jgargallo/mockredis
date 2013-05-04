from unittest import TestCase
from mockredis import MockRedis, mock_redis_client, mock_strict_redis_client


class TestFactories(TestCase):

    def test_mock_redis_client(self):
        """
        Test that we can pass kwargs to the Redis mock/patch target.
        """
        self.assertFalse(mock_redis_client(host="localhost", port=6379).strict)

    def test_mock_strict_redis_client(self):
        """
        Test that we can pass kwargs to the StrictRedis mock/patch target.
        """
        self.assertTrue(mock_strict_redis_client(host="localhost", port=6379).strict)


class TestRedis(TestCase):

    def setUp(self):
        self.redis = MockRedis()
        self.redis.flushdb()

    def test_get(self):
        self.assertEqual(None, self.redis.get('key'))

        self.redis.redis['key'] = 'value'
        self.assertEqual('value', self.redis.get('key'))

    def test_set(self):
        self.assertEqual(None, self.redis.redis.get('key'))

        self.redis.set('key', 'value')
        self.assertEqual('value', self.redis.redis.get('key'))

    def test_get_types(self):
        '''
        testing type coversions for set/get, hset/hget, sadd/smembers

        Python bools, lists, dicts are returned as strings by
        redis-py/redis.
        '''

        values = list([
            True,
            False,
            [1, '2'],
            {
                'a': 1,
                'b': 'c'
            },
        ])

        self.assertEqual(None, self.redis.get('key'))

        for value in values:
            self.redis.set('key', value)
            self.assertEqual(str(value),
                             self.redis.get('key'),
                             "redis.get")

            self.redis.hset('hkey', 'item', value)
            self.assertEqual(str(value),
                             self.redis.hget('hkey', 'item'))

            self.redis.sadd('skey', value)
            self.assertEqual(set([str(value)]),
                             self.redis.smembers('skey'))

            self.redis.flushdb()

    def test_incr(self):
        '''
        incr, hincr when keys exist
        '''

        values = list([
            (1, '2'),
            ('1', '2'),
        ])

        for value in values:
            self.redis.set('key', value[0])
            self.redis.incr('key')
            self.assertEqual(value[1],
                             self.redis.get('key'),
                             "redis.incr")

            self.redis.hset('hkey', 'attr', value[0])
            self.redis.hincrby('hkey', 'attr')
            self.assertEqual(value[1],
                             self.redis.hget('hkey', 'attr'),
                             "redis.hincrby")

            self.redis.flushdb()

    def test_incr_init(self):
        '''
        incr, hincr, decr when keys do NOT exist
        '''

        self.redis.incr('key')
        self.assertEqual('1', self.redis.get('key'))

        self.redis.hincrby('hkey', 'attr')
        self.assertEqual('1', self.redis.hget('hkey', 'attr'))

        self.redis.decr('dkey')
        self.assertEqual('-1', self.redis.get('dkey'))

    def test_ttl(self):
        self.redis.set('key', 'key')
        self.redis.expire('key', 30)

        assert self.redis.ttl('key') <= 30
        self.assertEqual(self.redis.ttl('invalid_key'), -1)

    def test_push_pop_returns_str(self):
        key = 'l'
        values = ['5', 5, [], {}]
        for v in values:
            self.redis.rpush(key, v)
            self.assertEquals(self.redis.lpop(key),
                              str(v))

    #### SET TESTS ####

    def test_sadd(self):
        key = "set"
        values = ["one", "uno", "two", "three"]
        for value in values:
            self.assertEquals(1, self.redis.sadd(key, value))

    def test_sadd_multiple(self):
        key = "set"
        values = ["one", "uno", "two", "three"]
        self.assertEquals(4, self.redis.sadd(key, *values))

    def test_sadd_duplicate_key(self):
        key = "set"
        self.assertEquals(1, self.redis.sadd(key, "one"))
        self.assertEquals(0, self.redis.sadd(key, "one"))

    def test_scard(self):
        key = "set"
        self.assertEquals(0, self.redis.scard(key))
        self.assertFalse(key in self.redis.redis)
        values = ["one", "uno", "two", "three"]
        self.assertEquals(4, self.redis.sadd(key, *values))
        self.assertEquals(4, self.redis.scard(key))

    def test_sdiff(self):
        self.redis.sadd("x", "one", "two", "three")
        self.redis.sadd("y", "one")
        self.redis.sadd("z", "two")

        with self.assertRaises(Exception):
            self.redis.sdiff([])

        self.assertEquals(set(), self.redis.sdiff("w"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.sdiff("x"))
        self.assertEquals(set(["two", "three"]), self.redis.sdiff("x", "y"))
        self.assertEquals(set(["two", "three"]), self.redis.sdiff(["x", "y"]))
        self.assertEquals(set(["three"]), self.redis.sdiff("x", "y", "z"))
        self.assertEquals(set(["three"]), self.redis.sdiff(["x", "y"], "z"))

    def test_sdiffstore(self):
        self.redis.sadd("x", "one", "two", "three")
        self.redis.sadd("y", "one")
        self.redis.sadd("z", "two")

        with self.assertRaises(Exception):
            self.redis.sdiffstore("w", [])

        self.assertEquals(3, self.redis.sdiffstore("w", "x"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.smembers("w"))

        self.assertEquals(2, self.redis.sdiffstore("w", "x", "y"))
        self.assertEquals(set(["two", "three"]), self.redis.smembers("w"))
        self.assertEquals(2, self.redis.sdiffstore("w", ["x", "y"]))
        self.assertEquals(set(["two", "three"]), self.redis.smembers("w"))
        self.assertEquals(1, self.redis.sdiffstore("w", "x", "y", "z"))
        self.assertEquals(set(["three"]), self.redis.smembers("w"))
        self.assertEquals(1, self.redis.sdiffstore("w", ["x", "y"], "z"))
        self.assertEquals(set(["three"]), self.redis.smembers("w"))

    def test_sinter(self):
        self.redis.sadd("x", "one", "two", "three")
        self.redis.sadd("y", "one")
        self.redis.sadd("z", "two")

        with self.assertRaises(Exception):
            self.redis.sinter([])

        self.assertEquals(set(), self.redis.sinter("w"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.sinter("x"))
        self.assertEquals(set(["one"]), self.redis.sinter("x", "y"))
        self.assertEquals(set(["two"]), self.redis.sinter(["x", "z"]))
        self.assertEquals(set(), self.redis.sinter("x", "y", "z"))
        self.assertEquals(set(), self.redis.sinter(["x", "y"], "z"))

    def test_sinterstore(self):
        self.redis.sadd("x", "one", "two", "three")
        self.redis.sadd("y", "one")
        self.redis.sadd("z", "two")

        with self.assertRaises(Exception):
            self.redis.sinterstore("w", [])

        self.assertEquals(3, self.redis.sinterstore("w", "x"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.smembers("w"))

        self.assertEquals(1, self.redis.sinterstore("w", "x", "y"))
        self.assertEquals(set(["one"]), self.redis.smembers("w"))
        self.assertEquals(1, self.redis.sinterstore("w", ["x", "z"]))
        self.assertEquals(set(["two"]), self.redis.smembers("w"))
        self.assertEquals(0, self.redis.sinterstore("w", "x", "y", "z"))
        self.assertEquals(set(), self.redis.smembers("w"))
        self.assertEquals(0, self.redis.sinterstore("w", ["x", "y"], "z"))
        self.assertEquals(set(), self.redis.smembers("w"))

    def test_sismember(self):
        key = "set"
        self.assertEquals(0, self.redis.sismember(key, "one"))
        self.assertFalse(key in self.redis.redis)
        self.assertEquals(1, self.redis.sadd(key, "one"))
        self.assertEquals(1, self.redis.sismember(key, "one"))
        self.assertEquals(0, self.redis.sismember(key, "two"))

    def test_smembers(self):
        key = "set"
        self.assertEquals(set(), self.redis.smembers(key))
        self.assertFalse(key in self.redis.redis)
        self.assertEquals(1, self.redis.sadd(key, "one"))
        self.assertEquals(set(["one"]), self.redis.smembers(key))
        self.assertEquals(1, self.redis.sadd(key, "two"))
        self.assertEquals(set(["one", "two"]), self.redis.smembers(key))

    def test_smove(self):
        self.assertEquals(0, self.redis.smove("x", "y", "one"))

        self.assertEquals(2, self.redis.sadd("x", "one", "two"))
        self.assertEquals(set(["one", "two"]), self.redis.smembers("x"))
        self.assertEquals(set(), self.redis.smembers("y"))

        self.assertEquals(0, self.redis.smove("x", "y", "three"))
        self.assertEquals(set(["one", "two"]), self.redis.smembers("x"))
        self.assertEquals(set(), self.redis.smembers("y"))

        self.assertEquals(1, self.redis.smove("x", "y", "one"))
        self.assertEquals(set(["two"]), self.redis.smembers("x"))
        self.assertEquals(set(["one"]), self.redis.smembers("y"))

    def test_spop(self):
        key = "set"
        self.assertEquals(None, self.redis.spop(key))
        self.assertEquals(1, self.redis.sadd(key, "one"))
        self.assertEquals("one", self.redis.spop(key))
        self.assertEquals(0, self.redis.scard(key))
        self.assertEquals(1, self.redis.sadd(key, "one"))
        self.assertEquals(1, self.redis.sadd(key, "two"))
        first = self.redis.spop(key)
        self.assertTrue(first in ["one", "two"])
        self.assertEquals(1, self.redis.scard(key))
        second = self.redis.spop(key)
        self.assertEquals("one" if first == "two" else "two", second)
        self.assertEquals(0, self.redis.scard(key))

    def test_srandmember(self):
        key = "set"
        # count is None
        self.assertEquals(None, self.redis.srandmember(key))
        self.assertEquals(1, self.redis.sadd(key, "one"))
        self.assertEquals("one", self.redis.srandmember(key))
        self.assertEquals(1, self.redis.scard(key))
        self.assertEquals(1, self.redis.sadd(key, "two"))
        self.assertTrue(self.redis.srandmember(key) in ["one", "two"])
        self.assertEquals(2, self.redis.scard(key))
        # count > 0
        self.assertEquals([], self.redis.srandmember("empty", 1))
        self.assertTrue(self.redis.srandmember(key, 1)[0] in ["one", "two"])
        self.assertEquals(set(["one", "two"]), set(self.redis.srandmember(key, 2)))
        # count < 0
        self.assertEquals([], self.redis.srandmember("empty", -1))
        self.assertTrue(self.redis.srandmember(key, -1)[0] in ["one", "two"])
        members = self.redis.srandmember(key, -2)
        self.assertEquals(2, len(members))
        for member in members:
            self.assertTrue(member in ["one", "two"])

    def test_srem(self):
        key = "set"
        self.assertEquals(0, self.redis.srem(key, "one"))
        self.assertEquals(3, self.redis.sadd(key, "one", "two", "three"))
        self.assertEquals(0, self.redis.srem(key, "four"))
        self.assertEquals(2, self.redis.srem(key, "one", "three"))
        self.assertEquals(1, self.redis.srem(key, "two", "four"))

    def test_sunion(self):
        self.redis.sadd("x", "one", "two", "three")
        self.redis.sadd("y", "one")
        self.redis.sadd("z", "two")

        with self.assertRaises(Exception):
            self.redis.sunion([])

        self.assertEquals(set(), self.redis.sunion("v"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.sunion("x"))
        self.assertEquals(set(["one"]), self.redis.sunion("v", "y"))
        self.assertEquals(set(["one", "two"]), self.redis.sunion(["y", "z"]))
        self.assertEquals(set(["one", "two", "three"]), self.redis.sunion("x", "y", "z"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.sunion(["x", "y"], "z"))

    def test_sunionstore(self):
        self.redis.sadd("x", "one", "two", "three")
        self.redis.sadd("y", "one")
        self.redis.sadd("z", "two")

        with self.assertRaises(Exception):
            self.redis.sunionstore("w", [])

        self.assertEquals(0, self.redis.sunionstore("w", "v"))
        self.assertEquals(set(), self.redis.smembers("w"))

        self.assertEquals(3, self.redis.sunionstore("w", "x"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.smembers("w"))

        self.assertEquals(1, self.redis.sunionstore("w", "v", "y"))
        self.assertEquals(set(["one"]), self.redis.smembers("w"))

        self.assertEquals(2, self.redis.sunionstore("w", ["y", "z"]))
        self.assertEquals(set(["one", "two"]), self.redis.smembers("w"))

        self.assertEquals(3, self.redis.sunionstore("w", "x", "y", "z"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.smembers("w"))

        self.assertEquals(3, self.redis.sunionstore("w", ["x", "y"], "z"))
        self.assertEquals(set(["one", "two", "three"]), self.redis.smembers("w"))

    #### SORTED SET TESTS ####

    def test_zadd(self):
        key = "zset"
        values = [("one", 1), ("uno", 1), ("two", 2), ("three", 3)]
        for member, score in values:
            self.assertEquals(1, self.redis.zadd(key, member, score))

    def test_zadd_strict(self):
        """Argument order for zadd depends on strictness"""
        self.redis.strict = True
        key = "zset"
        values = [("one", 1), ("uno", 1), ("two", 2), ("three", 3)]
        for member, score in values:
            self.assertEquals(1, self.redis.zadd(key, score, member))

    def test_zadd_duplicate_key(self):
        key = "zset"
        self.assertEquals(1, self.redis.zadd(key, "one", 1.0))
        self.assertEquals(0, self.redis.zadd(key, "one", 2.0))

    def test_zadd_wrong_type(self):
        key = "zset"
        self.redis.set(key, "value")
        with self.assertRaises(Exception):
            self.redis.zadd(key, "one", 2.0)

    def test_zadd_multiple_bad_args(self):
        key = "zset"
        args = ["one", 1, "two"]
        with self.assertRaises(Exception):
            self.redis.zadd(key, *args)

    def test_zadd_multiple_bad_score(self):
        key = "zset"
        with self.assertRaises(Exception):
            self.redis.zadd(key, "one", "two")

    def test_zadd_multiple_args(self):
        key = "zset"
        args = ["one", 1, "uno", 1, "two", 2, "three", 3]
        self.assertEquals(4, self.redis.zadd(key, *args))

    def test_zadd_multiple_kwargs(self):
        key = "zset"
        kwargs = {"one": 1, "uno": 1, "two": 2, "three": 3}
        self.assertEquals(4, self.redis.zadd(key, **kwargs))

    def test_zcard(self):
        key = "zset"
        self.assertEquals(0, self.redis.zcard(key))
        self.redis.zadd(key, "one", 1)
        self.assertEquals(1, self.redis.zcard(key))
        self.redis.zadd(key, "one", 2)
        self.assertEquals(1, self.redis.zcard(key))
        self.redis.zadd(key, "two", 2)
        self.assertEquals(2, self.redis.zcard(key))

    def test_zincrby(self):
        key = "zset"
        self.assertEquals(1.0, self.redis.zincrby(key, "member1"))
        self.assertEquals(2.0, self.redis.zincrby(key, "member2", 2))
        self.assertEquals(-1.0, self.redis.zincrby(key, "member1", -2))

    def test_zrange(self):
        key = "zset"
        self.assertEquals([], self.redis.zrange(key, 0, -1))
        self.redis.zadd(key, "one", 1.5)
        self.redis.zadd(key, "two", 2.5)
        self.redis.zadd(key, "three", 3.5)

        # full range
        self.assertEquals(["one", "two", "three"],
                          self.redis.zrange(key, 0, -1))
        # withscores
        self.assertEquals([("one", 1.5), ("two", 2.5), ("three", 3.5)],
                          self.redis.zrange(key, 0, -1, withscores=True))
        # score_cast_func
        self.assertEquals([("one", 1), ("two", 2), ("three", 3)],
                          self.redis.zrange(key, 0, -1, withscores=True, score_cast_func=int))

        # positive ranges
        self.assertEquals(["one"], self.redis.zrange(key, 0, 0))
        self.assertEquals(["one", "two"], self.redis.zrange(key, 0, 1))
        self.assertEquals(["one", "two", "three"], self.redis.zrange(key, 0, 2))
        self.assertEquals(["one", "two", "three"], self.redis.zrange(key, 0, 3))
        self.assertEquals(["two", "three"], self.redis.zrange(key, 1, 2))
        self.assertEquals(["three"], self.redis.zrange(key, 2, 3))

        # negative ends
        self.assertEquals(["one", "two", "three"], self.redis.zrange(key, 0, -1))
        self.assertEquals(["one", "two"], self.redis.zrange(key, 0, -2))
        self.assertEquals(["one"], self.redis.zrange(key, 0, -3))
        self.assertEquals([], self.redis.zrange(key, 0, -4))

        # negative starts
        self.assertEquals([], self.redis.zrange(key, -1, 0))
        self.assertEquals(["three"], self.redis.zrange(key, -1, -1))
        self.assertEquals(["two", "three"], self.redis.zrange(key, -2, -1))
        self.assertEquals(["one", "two", "three"], self.redis.zrange(key, -3, -1))
        self.assertEquals(["one", "two", "three"], self.redis.zrange(key, -4, -1))

        # desc
        self.assertEquals(["three", "two", "one"], self.redis.zrange(key, 0, 2, desc=True))
        self.assertEquals(["two", "one"], self.redis.zrange(key, 1, 2, desc=True))
        self.assertEquals(["three", "two"], self.redis.zrange(key, 0, 1, desc=True))

    def test_zrem(self):
        key = "zset"
        self.assertFalse(self.redis.zrem(key, "two"))

        self.redis.zadd(key, "one", 1.0)
        self.assertEquals(1, self.redis.zcard(key))

        self.assertTrue(self.redis.zrem(key, "one"))
        self.assertEquals(0, self.redis.zcard(key))

    def test_zscore(self):
        key = "zset"
        self.assertEquals(None, self.redis.zscore(key, "one"))

        self.redis.zadd(key, "one", 1.0)
        self.assertEquals(1.0, self.redis.zscore(key, "one"))

    def test_zrank(self):
        key = "zset"
        self.assertEquals(None, self.redis.zrank(key, "two"))

        self.redis.zadd(key, "one", 1.0)
        self.redis.zadd(key, "two", 2.0)
        self.assertEquals(0, self.redis.zrank(key, "one"))
        self.assertEquals(1, self.redis.zrank(key, "two"))

    def test_zcount(self):
        key = "zset"
        self.assertEquals(0, self.redis.zcount(key, "-inf", "inf"))

        self.redis.zadd(key, "one", 1.0)
        self.redis.zadd(key, "two", 2.0)

        self.assertEquals(2, self.redis.zcount(key, "-inf", "inf"))
        self.assertEquals(1, self.redis.zcount(key, "-inf", 1.0))
        self.assertEquals(1, self.redis.zcount(key, "-inf", 1.5))
        self.assertEquals(2, self.redis.zcount(key, "-inf", 2.0))
        self.assertEquals(2, self.redis.zcount(key, "-inf", 2.5))
        self.assertEquals(1, self.redis.zcount(key, 0.5, 1.0))
        self.assertEquals(1, self.redis.zcount(key, 0.5, 1.5))
        self.assertEquals(2, self.redis.zcount(key, 0.5, 2.0))
        self.assertEquals(2, self.redis.zcount(key, 0.5, 2.5))
        self.assertEquals(2, self.redis.zcount(key, 0.5, "inf"))

        self.assertEquals(0, self.redis.zcount(key, "inf", "-inf"))
        self.assertEquals(0, self.redis.zcount(key, 2.0, 0.5))

    def test_zrangebyscore(self):
        key = "zset"
        self.assertEquals([], self.redis.zrangebyscore(key, "-inf", "inf"))
        self.redis.zadd(key, "one", 1.5)
        self.redis.zadd(key, "two", 2.5)
        self.redis.zadd(key, "three", 3.5)

        self.assertEquals(["one", "two", "three"],
                          self.redis.zrangebyscore(key, "-inf", "inf"))
        self.assertEquals([("one", 1.5), ("two", 2.5), ("three", 3.5)],
                          self.redis.zrangebyscore(key, "-inf", "inf", withscores=True))
        self.assertEquals([("one", 1), ("two", 2), ("three", 3)],
                          self.redis.zrangebyscore(key, "-inf", "inf", withscores=True, score_cast_func=int))

        self.assertEquals(["one"],
                          self.redis.zrangebyscore(key, 1.0, 2.0))
        self.assertEquals(["one", "two"],
                          self.redis.zrangebyscore(key, 1.0, 3.0))
        self.assertEquals(["one"],
                          self.redis.zrangebyscore(key, 1.0, 3.0, start=0, num=1))
        self.assertEquals(["two"],
                          self.redis.zrangebyscore(key, 1.0, 3.0, start=1, num=1))
        self.assertEquals(["two", "three"],
                          self.redis.zrangebyscore(key, 1.0, 3.5, start=1, num=4))
        self.assertEquals([],
                          self.redis.zrangebyscore(key, 1.0, 3.5, start=3, num=4))

    def test_zremrank(self):
        key = "zset"
        self.assertEquals(None, self.redis.zrevrank(key, "two"))

        self.redis.zadd(key, "one", 1.0)
        self.redis.zadd(key, "two", 2.0)
        self.assertEquals(1, self.redis.zrevrank(key, "one"))
        self.assertEquals(0, self.redis.zrevrank(key, "two"))

    def test_zrevrangebyscore(self):
        key = "zset"
        self.assertEquals([], self.redis.zrevrangebyscore(key, "inf", "-inf"))
        self.redis.zadd(key, "one", 1.5)
        self.redis.zadd(key, "two", 2.5)
        self.redis.zadd(key, "three", 3.5)

        self.assertEquals(["three", "two", "one"],
                          self.redis.zrevrangebyscore(key, "inf", "-inf"))
        self.assertEquals([("three", 3.5), ("two", 2.5), ("one", 1.5)],
                          self.redis.zrevrangebyscore(key, "inf", "-inf", withscores=True))
        self.assertEquals([("three", 3), ("two", 2), ("one", 1)],
                          self.redis.zrevrangebyscore(key, "inf", "-inf", withscores=True, score_cast_func=int))

        self.assertEquals(["one"],
                          self.redis.zrevrangebyscore(key, 2.0, 1.0))
        self.assertEquals(["two", "one"],
                          self.redis.zrevrangebyscore(key, 3.0, 1.0))
        self.assertEquals(["two"],
                          self.redis.zrevrangebyscore(key, 3.0, 1.0, start=0, num=1))
        self.assertEquals(["one"],
                          self.redis.zrevrangebyscore(key, 3.0, 1.0, start=1, num=1))
        self.assertEquals(["two", "one"],
                          self.redis.zrevrangebyscore(key, 3.5, 1.0, start=1, num=4))
        self.assertEquals([],
                          self.redis.zrevrangebyscore(key, 3.5, 1.0, start=3, num=4))

    def test_zremrangebyrank(self):
        key = "zset"
        self.assertEquals(0, self.redis.zremrangebyrank(key, 0, -1))

        self.redis.zadd(key, "one", 1.0)
        self.redis.zadd(key, "two", 2.0)
        self.redis.zadd(key, "three", 3.0)

        self.assertEquals(2, self.redis.zremrangebyrank(key, 0, 1))

        self.assertEquals(["three"], self.redis.zrange(key, 0, -1))
        self.assertEquals(1, self.redis.zremrangebyrank(key, 0, -1))

        self.assertEquals([], self.redis.zrange(key, 0, -1))

    def test_zremrangebyscore(self):
        key = "zset"
        self.assertEquals(0, self.redis.zremrangebyscore(key, "-inf", "inf"))

        self.redis.zadd(key, "one", 1.0)
        self.redis.zadd(key, "two", 2.0)
        self.redis.zadd(key, "three", 3.0)

        self.assertEquals(1, self.redis.zremrangebyscore(key, 0, 1))

        self.assertEquals(["two", "three"], self.redis.zrange(key, 0, -1))
        self.assertEquals(2, self.redis.zremrangebyscore(key, 2.0, "inf"))

        self.assertEquals([], self.redis.zrange(key, 0, -1))

    def test_zunionstore(self):
        key = "zset"

        # no keys
        self.assertEquals(0, self.redis.zunionstore(key, ["zset1", "zset2"]))

        self.redis.zadd("zset1", "one", 1.0)
        self.redis.zadd("zset1", "two", 2.0)
        self.redis.zadd("zset2", "two", 2.5)
        self.redis.zadd("zset2", "three", 3.0)

        # sum (default)
        self.assertEquals(3, self.redis.zunionstore(key, ["zset1", "zset2"]))
        self.assertEquals([("one", 1.0), ("three", 3.0), ("two", 4.5)],
                          self.redis.zrange(key, 0, -1, withscores=True))

        self.redis.zadd("zset1", "one", 1.0)
        self.redis.zadd("zset1", "two", 2.0)
        self.redis.zadd("zset2", "two", 2.5)
        self.redis.zadd("zset2", "three", 3.0)

        # sum (explicit)
        self.assertEquals(3, self.redis.zunionstore(key, ["zset1", "zset2"], aggregate="sum"))
        self.assertEquals([("one", 1.0), ("three", 3.0), ("two", 4.5)],
                          self.redis.zrange(key, 0, -1, withscores=True))

        self.redis.zadd("zset1", "one", 1.0)
        self.redis.zadd("zset1", "two", 2.0)
        self.redis.zadd("zset2", "two", 2.5)
        self.redis.zadd("zset2", "three", 3.0)

        # min
        self.assertEquals(3, self.redis.zunionstore(key, ["zset1", "zset2"], aggregate="min"))
        self.assertEquals([("one", 1.0), ("two", 2.0), ("three", 3.0)],
                          self.redis.zrange(key, 0, -1, withscores=True))

        self.redis.zadd("zset1", "one", 1.0)
        self.redis.zadd("zset1", "two", 2.0)
        self.redis.zadd("zset2", "two", 2.5)
        self.redis.zadd("zset2", "three", 3.0)

        # max
        self.assertEquals(3, self.redis.zunionstore(key, ["zset1", "zset2"], aggregate="max"))
        self.assertEquals([("one", 1.0), ("two", 2.5), ("three", 3.0)],
                          self.redis.zrange(key, 0, -1, withscores=True))

    def test_zinterstore(self):
        key = "zset"

        # no keys
        self.assertEquals(0, self.redis.zinterstore(key, ["zset1", "zset2"]))

        self.redis.zadd("zset1", "one", 1.0)
        self.redis.zadd("zset1", "two", 2.0)
        self.redis.zadd("zset2", "two", 2.5)
        self.redis.zadd("zset2", "three", 3.0)

        # sum (default)
        self.assertEquals(1, self.redis.zinterstore(key, ["zset1", "zset2"]))
        self.assertEquals([("two", 4.5)],
                          self.redis.zrange(key, 0, -1, withscores=True))

        self.redis.zadd("zset1", "one", 1.0)
        self.redis.zadd("zset1", "two", 2.0)
        self.redis.zadd("zset2", "two", 2.5)
        self.redis.zadd("zset2", "three", 3.0)

        # sum (explicit)
        self.assertEquals(1, self.redis.zinterstore(key, ["zset1", "zset2"], aggregate="sum"))
        self.assertEquals([("two", 4.5)],
                          self.redis.zrange(key, 0, -1, withscores=True))

        self.redis.zadd("zset1", "one", 1.0)
        self.redis.zadd("zset1", "two", 2.0)
        self.redis.zadd("zset2", "two", 2.5)
        self.redis.zadd("zset2", "three", 3.0)

        # min
        self.assertEquals(1, self.redis.zinterstore(key, ["zset1", "zset2"], aggregate="min"))
        self.assertEquals([("two", 2.0)],
                          self.redis.zrange(key, 0, -1, withscores=True))

        self.redis.zadd("zset1", "one", 1.0)
        self.redis.zadd("zset1", "two", 2.0)
        self.redis.zadd("zset2", "two", 2.5)
        self.redis.zadd("zset2", "three", 3.0)

        # max
        self.assertEquals(1, self.redis.zinterstore(key, ["zset1", "zset2"], aggregate="max"))
        self.assertEquals([("two", 2.5)],
                          self.redis.zrange(key, 0, -1, withscores=True))

    ### Hash Tests ###

    def test_hexists(self):
        hashkey = "hash"
        self.assertEquals(False, self.redis.hexists(hashkey, "key"))
        self.redis.hset(hashkey, "key", "value")
        self.assertEquals(True, self.redis.hexists(hashkey, "key"))
        self.assertEquals(False, self.redis.hexists(hashkey, "key2"))

    def test_hgetall(self):
        hashkey = "hash"
        self.assertEquals({}, self.redis.hgetall(hashkey))
        self.redis.hset(hashkey, "key", "value")
        self.assertEquals({"key": "value"}, self.redis.hgetall(hashkey))

    def test_hdel(self):
        hashkey = "hash"
        self.redis.hmset(hashkey, {1: 1, 2: 2, 3: 3})
        self.assertEquals(0, self.redis.hdel(hashkey, "foo"))
        self.assertEquals({"1": "1", "2": "2", "3": "3"}, self.redis.hgetall(hashkey))
        self.assertEquals(2, self.redis.hdel(hashkey, "1", 2))
        self.assertEquals({"3": "3"}, self.redis.hgetall(hashkey))
        self.assertEquals(1, self.redis.hdel(hashkey, "3", 4))
        self.assertEquals({}, self.redis.hgetall(hashkey))

    def test_hlen(self):
        hashkey = "hash"
        self.assertEquals(0, self.redis.hlen(hashkey))
        self.redis.hset(hashkey, "key", "value")
        self.assertEquals(1, self.redis.hlen(hashkey))

    def test_hset(self):
        hashkey = "hash"
        self.redis.hset(hashkey, "key", "value")
        self.assertEquals("value", self.redis.hget(hashkey, "key"))

    def test_hset_integral(self):
        hashkey = "hash"
        self.redis.hset(hashkey, 1, 2)
        self.assertEquals("2", self.redis.hget(hashkey, 1))
        self.assertEquals("2", self.redis.hget(hashkey, "1"))

    def test_hsetnx(self):
        hashkey = "hash"
        self.assertEquals(1, self.redis.hsetnx(hashkey, "key", "value1"))
        self.assertEquals("value1", self.redis.hget(hashkey, "key"))
        self.assertEquals(0, self.redis.hsetnx(hashkey, "key", "value2"))
        self.assertEquals("value1", self.redis.hget(hashkey, "key"))

    def test_hmset(self):
        hashkey = "hash"
        self.redis.hmset(hashkey, {"key1": "value1", "key2": "value2"})
        self.assertEquals("value1", self.redis.hget(hashkey, "key1"))
        self.assertEquals("value2", self.redis.hget(hashkey, "key2"))

    def test_hmset_integral(self):
        hashkey = "hash"
        self.redis.hmset(hashkey, {1: 2, 3: 4})
        self.assertEquals("2", self.redis.hget(hashkey, "1"))
        self.assertEquals("2", self.redis.hget(hashkey, 1))
        self.assertEquals("4", self.redis.hget(hashkey, "3"))
        self.assertEquals("4", self.redis.hget(hashkey, 3))

    def test_hmget(self):
        hashkey = "hash"
        self.redis.hmset(hashkey, {1: 2, 3: 4})
        self.assertEquals(["2", None, "4"], self.redis.hmget(hashkey, "1", "2", "3"))
        self.assertEquals(["2", None, "4"], self.redis.hmget(hashkey, ["1", "2", "3"]))
        self.assertEquals(["2", None, "4"], self.redis.hmget(hashkey, [1, 2, 3]))

    def test_hincrby(self):
        hashkey = "hash"
        self.assertEquals(1, self.redis.hincrby(hashkey, "key", 1))
        self.assertEquals(3, self.redis.hincrby(hashkey, "key", 2))
        self.assertEquals("3", self.redis.hget(hashkey, "key"))

    def test_hincrbyfloat(self):
        hashkey = "hash"
        self.assertEquals(1.2, self.redis.hincrbyfloat(hashkey, "key", 1.2))
        self.assertEquals(3.5, self.redis.hincrbyfloat(hashkey, "key", 2.3))
        self.assertEquals("3.5", self.redis.hget(hashkey, "key"))

    def test_hkeys(self):
        hashkey = "hash"
        self.redis.hmset(hashkey, {1: 2, 3: 4})
        self.assertEquals(["1", "3"], sorted(self.redis.hkeys(hashkey)))

    def test_hvals(self):
        hashkey = "hash"
        self.redis.hmset(hashkey, {1: 2, 3: 4})
        self.assertEquals(["2", "4"], sorted(self.redis.hvals(hashkey)))
