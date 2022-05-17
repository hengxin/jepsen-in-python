import time
import pprint
import random
from generator import interpreter
from generator import generator as gen
from util import util
from util.globalvars import GlobalVars
from fastcore.transform import Pipeline
from functools import partial


class TestInterpreter:
    class StubClient:
        def __init__(self, a=None, b=None):
            self.a = a
            self.b = b

        def setup_db(self):
            return

        def shutdown_db(self):
            return

        def is_running(self):
            return

        def connect_db(self):
            return

        def disconnect_db(self):
            return

        def operate(self, op):
            # time.sleep(0.01)
            response_op = {
                "type": random.choice(['ok', 'info', 'fail']),
                "value": "foo",
                "process": op["process"]
            }
            return response_op

    class StubNemesis:
        def start(self):
            return {"type": "info", "f": "start", "value": "start nemesis", "process": "nemesis"}

        def stop(self):
            return {"type": "info", "f": "stop", "value": "stop nemesis", "process": "nemesis"}

        def recover(self):
            return {"type": "info", "f": "recover", "value": "recover", "process": "nemesis"}

    def test_run(self):
        config = {
            "concurrency": 10,
            "server": {"client1": "None", "client2": "None", "client3": "None", "client4": "None", "client5": "None"}
        }

        t = 1.0
        clients = [TestInterpreter.StubClient() for _ in range(len(config["server"].keys()))]
        nemesis = TestInterpreter.StubNemesis()
        GlobalVars.set_clients(clients)
        GlobalVars.set_nemesis(nemesis)

        class SelfIncVar:
            def __init__(self):
                self.val = 0

            def __iter__(self):
                self.val = 0
                return self

            def __next__(self):
                x = self.val
                self.val += 1
                return x

        """ test generator 1 """
        i = SelfIncVar()
        it = iter(i)
        generator1 = gen.phases(
            Pipeline([
                partial(gen.nemesis, gen.mix([
                    gen.repeat({"type": "info", "f": "start"}),
                    gen.repeat({"type": "info", "f": "stop"})
                ])),
                partial(gen.time_limit, t)
            ])(gen.reserve(
                2, lambda: {"f": "write", "value": next(it)},
                5, lambda: {"f": "cas", "value": [random.randint(0, 5), random.randint(0, 5)]},
                gen.repeat({"f": "read"})
            )),
            gen.log("Recovering"),
            gen.nemesis({"type": "info", "f": "recover"}),
            gen.sleep(0.1),
            gen.log("Done, final read"),
            gen.clients(gen.until_ok(lambda: {"f": "read"}))
        )

        """ test generator 2 """
        generator2 = Pipeline([
            partial(gen.nemesis, gen.mix([
                gen.repeat({"type": "info", "f": "start"}),
                gen.repeat({"type": "info", "f": "stop"})
            ])),
            partial(gen.time_limit, t)
        ])(gen.mix([
            lambda: {
                "type": "invoke",
                "f": "read",
                "value": None
            },
            lambda: {
                "type": "invoke",
                "f": "write",
                "value": str(random.randint(1, 5))
            },
            lambda: {
                "type": "invoke",
                "f": "cas",
                "value": [str(random.randint(1, 5)), str(random.randint(1, 5))]
            }]))

        config["generator"] = generator1

        history = util.with_relative_time(
            interpreter.run, config
        )

        nemesis_ops = list(filter(lambda op: op["process"] == "nemesis", history))
        client_ops = list(filter(lambda op: op["process"] != "nemesis", history))

        # pprint.pprint(client_ops)
        # pprint.pprint(nemesis_ops)

        # 经测试，generator 1 大约 5k/sec, generator 2 大约7.5k/sec
        # 根据机器性能不同可能会有浮动
        print("total ops: {}, client ops: {}, nemesis ops: {}".format(
            len(history),
            len(client_ops),
            len(nemesis_ops)
        ))


if __name__ == "__main__":
    ti = TestInterpreter()
    ti.test_run()
