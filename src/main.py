import requests
import logging
import base64
import time
import preprocessor
import classifier
import data_collector
import hyper_params


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


    # collect num_obs observations
    # uncomment below if data is needed
    #data_collector.collect(s, hyper_params.NUM_OBS, hyper_params.RAW_DATA_FILE)

    # create the preprocessor object
    preprocessor = preprocessor.Preprocessor() 

    # extract TF-IDF vector and populate feature matrix and label vector
    preprocessor.preprocess()

    # create the classifier object
    classifier = classifier.Classifier()
    
    # train the model given the collected observations and labels
    classifier.train(hyper_params.NUM_OBS, preprocessor.labels, preprocessor.tokens)

    for _ in range(100):
        # query the /challenge endpoint
        s.get()

        # preprocess the blob we want to classify
        obs_tfidf_vec = preprocessor.classification_preprocess(s.binary) 

        # make classification!
        target = classifier.classify(obs_tfidf_vec, s.targets)
        print(target)
        s.post(target)
        
        s.log.info("Guess:[{: >9}]   Answer:[{: >9}]   Wins:[{: >3}]"
                .format(target[0], s.ans, s.wins))
       
        # 500 consecutive correct answers are required to win
        # very very unlikely with current code
        if s.hash:
            s.log.info("You win! {}".format(s.hash))
            exit()

    
