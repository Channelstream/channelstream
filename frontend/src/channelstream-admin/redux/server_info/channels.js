'use strict';

export const types = {
    CHANNELS_SET: 'channelStats/SET'
};

const update = (state, mutations) => Object.assign({}, state, mutations);

export const actions = {
    set: (channels) => ({
        type: types.CHANNELS_SET,
        channels: channels
    })
};

const INITIAL_STATE = [];

export const reducer = (state = INITIAL_STATE, action) => {
    switch (action.type) {
        case types.CHANNELS_SET:
            state = [...action.channels];
            break;
    }
    return state;
};

export default reducer;
