import module.env as env


def is_admin(user_id: int) -> bool:
    return user_id == env.get_master_id() or user_id == env.get_dev_id()
