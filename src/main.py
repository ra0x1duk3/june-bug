import requests
import logging
import base64
import time
import preprocessor
import classifier

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Server(object):
    url = 'https://mlb.praetorian.com'
    log = logging.getLogger(__name__)

    def __init__(self):
        self.session = requests.session()
        self.binary  = None
        self.hash    = None
        self.wins    = 0
        self.targets = []

    def _request(self, route, method='get', data=None):
        while True:
            try:
                if method == 'get':
                    r = self.session.get(self.url + route)
                else:
                    r = self.session.post(self.url + route, data=data)
                if r.status_code == 429:
                    raise Exception('Rate Limit Exception')
                if r.status_code == 500:
                    raise Exception('Unknown Server Exception')

                return r.json()
            except Exception as e:
                self.log.error(e)
                self.log.info('Waiting 60 seconds before next request')
                time.sleep(60)

    def get(self):
        r = self._request("/challenge")
        self.targets = r.get('target', [])
        self.binary  = base64.b64decode(r.get('binary', ''))
        return r

    def post(self, target):
        r = self._request("/solve", method="post", data={"target": target})
        self.wins = r.get('correct', 0)
        self.hash = r.get('hash', self.hash)
        self.ans  = r.get('target', 'unknown')
        return r

if __name__ == "__main__":

    # create the server object
    s = Server()

    # create the preprocessor object
    preprocessor = preprocessor.Preprocessor()

    # create the classifier object
    classifier = classifier.Classifier()


    # collect 10,000,000 observations
    preprocessor.collect_data(s, 300000)
    raw_data = preprocessor.retreive_data()
    #preprocessor.tokenize("c90b1baa4600000c0aa61ade1b994600000c09a619f01b88a618f50c080605009100009098a0c02000a809910000c02000a9091b88a628e7810000c020009808")
    

    # train the model given the collected observations and labels
     
    for _ in range(10):
        # query the /challenge endpoint
        #s.get()
         
        #target = classifier.predict()
        #s.post(target)

        #s.log.info("Guess:[{: >9}]   Answer:[{: >9}]   Wins:[{: >3}]".format(target, s.ans, s.wins))
        

        # 500 consecutive correct answers are required to win
        # very very unlikely with current code
        if s.hash:
            s.log.info("You win! {}".format(s.hash))

