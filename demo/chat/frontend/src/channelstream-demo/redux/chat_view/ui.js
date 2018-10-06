'use strict';

export const types = {
    SET_VIEWIED_CHANNEL: 'chatView/ui/SET_VIEWIED_CHANNEL',
};

export const actions = {
    setViewedChannel: (channel) => ({
        type: types.SET_VIEWIED_CHANNEL,
        channel: channel
    })
};

const INITIAL_STATE = {
    selectedChannel: 'pub_chan',
    //what we can subscribe to
    possibleChannels: ['notify', 'pub_chan', 'second_channel'],
};


export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET_VIEWIED_CHANNEL:
            state = {
                possibleChannels: state.possibleChannels,
                selectedChannel: action.channel,
            };
            break;
    }
    return state;
};

export default reducer;
