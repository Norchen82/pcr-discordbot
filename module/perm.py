import module.cfg as cfg


def is_admin(user_id: int) -> bool:
    return user_id == cfg.master_id() or user_id == cfg.dev_id()
