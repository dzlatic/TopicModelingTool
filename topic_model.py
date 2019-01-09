



def get_inference_distribution(inference, text):
    topic_distribution =[]
    model_id=inference.model_id
    model = db_session.query(Model).filter_by(id=model_id).one()
    topics = model.topics
    for topic in topics:
        print("appending: id:{}, distribution: 0.05 ".format(topic.id))
        topic_distribution.append({"id":topic.id, "distribution": 0.05})
    print("APPENDED: {}".format(topic_distribution))
    return topic_distribution