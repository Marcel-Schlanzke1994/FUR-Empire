'use strict';
self.addEventListener('push', event => {
  let payload = {title:'FUR Empire',body:'Es gibt neue Informationen in deinem Imperium.',url:'/'};
  try {
    const supplied = event.data ? event.data.json() : {};
    if (supplied && supplied.title === 'FUR Empire' && supplied.url === '/') payload = supplied;
  } catch (_) { /* Ignore provider data and keep the generic local fallback. */ }
  event.waitUntil(self.registration.showNotification('FUR Empire', {
    body:'Es gibt neue Informationen in deinem Imperium.',
    tag:'fur-empire-update',
    data:{url:'/'},
    icon:'/static/favicon.svg',
    badge:'/static/favicon.svg'
  }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(clients => {
    for (const client of clients) if (new URL(client.url).origin === self.location.origin) return client.focus();
    return self.clients.openWindow('/');
  }));
});
self.addEventListener('pushsubscriptionchange', event => {
  event.waitUntil(self.registration.pushManager.getSubscription().then(subscription => {
    if (!subscription) return;
    return self.clients.matchAll({type:'window',includeUncontrolled:true}).then(clients => {
      const client = clients.find(item => new URL(item.url).origin === self.location.origin);
      if (client) client.postMessage({type:'fur-push-subscription-changed'});
    });
  }));
});
