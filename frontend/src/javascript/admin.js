import { Application } from "@hotwired/stimulus"
import ClassifierChooserController from "./controllers/classifier-chooser-controller.js"
import '../styles/admin.css'

const application = Application.start()

application.register("classifier-chooser", ClassifierChooserController)

if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  application.debug = true
  window.CLASSIFIER_DEBUG = true
}

window.StimulusFeathers = application

export { application }
