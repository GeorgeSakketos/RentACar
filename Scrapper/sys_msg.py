def system_message(msg_type: str) -> str:
    if (msg_type.upper() == "E"):
        return "[ERROR]"
    elif (msg_type.upper() == "I"):
        return "[INFO]"
    elif (msg_type.upper() == "S"):
        return "[SYSTEM]"
    elif (msg_type.upper() == "U"):
        return "[UNKNOWN]"
    else:
        raise ValueError(f"Message Type: Invalid type '{msg_type};. Expected 'E(RROR)', 'I(NFO)', 'S(YSTEM)', 'U(NKNOWN)'.")