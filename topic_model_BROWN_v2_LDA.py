import nltk

nltk.download('brown')
nltk.download('stopwords')
nltk.download('punkt')

from nltk.corpus import brown

data = []

for fileid in brown.fileids():
	document = ' '.join(brown.words(fileid))
	data.append(document)

NO_DOCUMENTS = len(data)
print(NO_DOCUMENTS)
print(data[:5])



import re
from gensim import models, corpora
from nltk import word_tokenize
from nltk.corpus import stopwords

NUM_TOPICS = 10
STOPWORDS = stopwords.words('english')
STOPWORDS.extend(['said', 'time', 'new', 'like', 'first', 'two', 'would', 'may',
                  'could', 'one', 'made', 'even', 'many', 'must', 'also', 'back',
                  'way', 'year', 'years', 'see', 'well', 'much', 'state', 'man',
                  'world', 'little', 'still', 'mrs.', 'men', 'make', 'get', 'long',
                  'know', 'states', 'people', 'life', 'good', 'work', 'might'])


def clean_text(text):
	tokenized_text = word_tokenize(text.lower())
	cleaned_text = [t for t in tokenized_text if t not in STOPWORDS and re.match('[a-zA-Z\-][a-zA-Z\-]{2,}', t)]
	return cleaned_text


# For gensim we need to tokenize the data and filter out stopwords
tokenized_data = []
for text in data:
	tokenized_data.append(clean_text(text))

# Build a Dictionary - association word to numeric id
dictionary = corpora.Dictionary(tokenized_data)

# Transform the collection of texts to a numerical form
corpus = [dictionary.doc2bow(text) for text in tokenized_data]

# Have a look at how the 20th document looks like: [(word_id, count), ...]
print(corpus[20])
# [(12, 3), (14, 1), (21, 1), (25, 5), (30, 2), (31, 5), (33, 1), (42, 1), (43, 2),  ...

print("started building the LDA model")
lda_model = models.LdaModel(corpus=corpus, num_topics=NUM_TOPICS, id2word=dictionary)
print("finished building the LDA model")
# Build the LSI model
# lsi_model = models.LsiModel(corpus=corpus, num_topics=NUM_TOPICS, id2word=dictionary)


print("LDA Model:")

for idx in range(NUM_TOPICS):
	# Print the first 10 most representative topics
	print("Topic #%s:" % idx, lda_model.print_topic(idx, 10))

print("=" * 20)

text = "The economy is working better than ever before."
bow = dictionary.doc2bow(clean_text(text))

print(lda_model[bow])
# [(0, 0.020005183), (1, 0.020005869), (2, 0.02000626), (3, 0.020005472), (4, 0.020009108), (5, 0.020005926), (6, 0.81994385), (7, 0.020006068), (8, 0.020006327), (9, 0.020005994)]


# from gensim.test.utils import datapath
# temp_file = datapath("saved_model")

lda_model.save("./models/NLTK_BROWN_LDA_V2")
print("NLTK_BROWN_LDA_V2 model saved")


