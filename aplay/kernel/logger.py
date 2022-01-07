import logging

actor_logger = logging.getLogger(__package__)
actor_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
actor_logger.addHandler(handler)
