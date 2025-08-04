import { Application } from "@hotwired/stimulus"
import ClassifierModalController from "./controllers/classifier-modal-controller.js"
import '../styles/admin.css'

const application = Application.start()

application.register("classifier-modal", ClassifierModalController)

if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  application.debug = true
  window.CLASSIFIER_DEBUG = true
}

window.StimulusFeathers = application

document.addEventListener('DOMContentLoaded', function() {
  console.log('Wagtail Feathers admin JavaScript loaded')
  
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const classifierModals = node.querySelectorAll('[data-controller*="classifier-modal"]')
            if (classifierModals.length > 0) {
              console.log('Classifier modal detected, reinitializing Stimulus')
              application.load()
            }
          }
        })
      }
    })
  })
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  })
})

export { application }

