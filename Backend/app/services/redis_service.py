import redis 
import json 
from typing import Optional


class RedisCacheService:

    def __init__(self, host: str= "localhost", port: int =6379, db:int=0):
        self.redis_client = redis.Redis(host= host, port= port, decode_response= True)
    
    def set_answer(self, question: str, answer: str, ttl:int =3600):

        self.redis_client.set(question, json.dumps({"answer": answer}), ex= ttl)

    def get_answer(self, question: str) -> Optional[str]:

        cached= self.redis_client.get(question)
        if cached:
            return json.loads(cached)["answer"]
        return None
    
    def delete_answer(self, question: str):
        self.redis_client.delete(question)
    
    def clear_cache(self):
        self.redis_client.flushdb()
