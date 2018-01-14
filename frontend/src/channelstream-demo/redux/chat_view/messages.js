'use strict';

export const types = {
    SET_CHANNEL_MESSAGES: 'chatView/SET_CHANNEL_MESSAGES',
};

export const actions = {
    setChannelMessages: (messages) => ({
        type: types.SET_CHANNEL_MESSAGES,
        messages: messages
    })
};

const INITIAL_STATE = {
    //mapping of channels with messages
    channelMessages: {},
    //message objects
    messages: {},
    allIds: []
};


export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET_CHANNEL_MESSAGES:
            state = {
                messages: {...state.messages},
                allIds: [...state.allIds],
                channelMessages: {...state.channelMessages}
            };
            for (let messageInfo of Object.entries(action.messages)) {
                for (let msg of messageInfo[1]) {
                    state.messages[msg.uuid] = msg;
                    if (!state.channelMessages.hasOwnProperty(messageInfo[0])) {
                        state.channelMessages[messageInfo[0]] = [];
                    }
                    if (state.allIds.indexOf(msg.uuid) === -1) {
                        state.allIds.push(msg.uuid);
                        state.channelMessages[messageInfo[0]].push(msg.uuid);
                    }
                }
            }
            break;
    }
    return state;
};

export default reducer
