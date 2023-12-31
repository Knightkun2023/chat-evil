from flask import jsonify
from flask_babel import _
from . import app

@app.route('/translations.js')
def translations():
    translations = {
        'Content that expresses, incites, or promotes harassing language towards any target.': _('Content that expresses, incites, or promotes harassing language towards any target.'),
        'Harassment content that also includes violence or serious harm towards any target.': _('Harassment content that also includes violence or serious harm towards any target.'),
        'Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Hateful content aimed at non-protected groups (e.g., chess players) is harrassment.': _('Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Hateful content aimed at non-protected groups (e.g., chess players) is harrassment.'),
        'Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.': _('Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.'),
        'Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.': _('Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.'),
        'Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm, such as suicide, cutting, and eating disorders.': _('Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm, such as suicide, cutting, and eating disorders.'),
        'Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts.': _('Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts.'),
        'Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).': _('Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).'),
        'Sexual content that includes an individual who is under 18 years old.': _('Sexual content that includes an individual who is under 18 years old.'),
        'Content that depicts death, violence, or physical injury.': _('Content that depicts death, violence, or physical injury.'),
        'Content that depicts death, violence, or physical injury in graphic detail.': _('Content that depicts death, violence, or physical injury in graphic detail.')
    }
    return jsonify(translations)
