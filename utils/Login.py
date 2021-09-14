from wrapper.kiteext import KiteExt
import json

class Login:

    def loginkite(self):
        user = json.loads(open('./config/userzerodha.json','r').read().rstrip())
        kite = KiteExt()
        kite.login_with_credentials(
                userid=user['user_id'], password=user['password'], twofa=user['twofa'])
        enctoken = open('./config/enctoken.txt', 'r').read().rstrip()
        kite.set_headers(enctoken)
        return kite