"""Minimal MQTT broker for local development using amqtt."""
import asyncio
import logging
from amqtt.broker import Broker

logging.basicConfig(level=logging.WARNING)

config = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": "0.0.0.0:1883",
        },
    },
    "sys_interval": 0,
    "auth": {
        "allow-anonymous": True,
    },
    "topic-check": {
        "enabled": False,
    },
}


async def main():
    broker = Broker(config)
    print("[MQTT] Broker starting on port 1883...")
    await broker.start()
    print("[MQTT] Broker READY — listening on 1883")
    try:
        await asyncio.get_event_loop().create_future()  # run forever
    finally:
        await broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
