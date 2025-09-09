
class Timeout:
    def __init__(self):
        pass
    
    async def retry_step(self, step_name: str, func, *args, retries: int = 1, **kwargs):
            attempt = 0
            while True:
                try:
                    attempt += 1
                    print(f"➡️  Step: {step_name} (attempt {attempt})")
                    return await func(*args, **kwargs)
                except Exception as e:
                    if "TimeoutError" in str(type(e)) or "Timeout" in str(e):
                        if attempt <= retries:
                            print(f"⚠️  Timeout in {step_name}, retrying (attempt {attempt}/{retries+1})...")
                            continue
                        else:
                            print(f"❌ Failed {step_name} after {attempt} attempts: {e}")
                            raise
                    else:
                        # other error, don't retry
                        print(f"❌ Error in {step_name}: {e}")
                        raise