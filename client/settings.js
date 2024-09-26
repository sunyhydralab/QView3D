import Store from 'electron-store'

const store = new Store();

store.set('primaryColor', '#7561a9');
store.set('secondaryColor', '#60aeae');
store.set('backgroundColor', '#b9b9b9');
store.set('serverIpAddress', '127.0.0.1:8000')


const set = (key, value) => {
    store.set(key, value);
};

const get = (key) => {
    return store.get(key);
};

module.exports = { set, get };

