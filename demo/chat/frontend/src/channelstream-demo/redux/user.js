'use strict';

export const types = {
    SET: 'user/SET',
    SET_STATE: 'user/SET_STATE',
    SET_CHANNELS: 'user/SET_CHANNELS'
};

export const actions = {
    set: (values) => ({
        type: types.SET,
        values: values
    }),
    setChannels: (channels) => ({
        type: types.SET_CHANNELS,
        channels: channels
    }),
    setState: (state) => ({
        type: types.SET_STATE,
        state: state
    })
};

const INITIAL_STATE = {
    username: 'Anon-' + String(Math.floor(Math.random() * 10000)),
    anonymous: true,
    email: '',
    subscribedChannels: ['pub_chan'],
    state: {}
};

export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET:
            state = {
                ...state,
                subscribedChannels: [...state.subscribedChannels],
                state: {...state.state},
                ...action.values
            };
            state.anonymous = state.username.indexOf('Anon-') !== -1;
            break;
        case types.SET_STATE:
            state = {...state, state: {...action.state}};
            break;
        case types.SET_CHANNELS:
            state = {...state, subscribedChannels: action.channels};
            break;
    }
    return state;
};

export default reducer
