'use strict';

export const types = {
    SET_USER_STATES: 'chatView/SET_USER_STATES',
};

export const actions = {
    setUserStates: (states) => ({
        type: types.SET_USER_STATES,
        states: states
    })
};

const INITIAL_STATE = {states: {}, allIds: []};


export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET_USER_STATES:
            state = {
                states: {...state.states},
                allIds: [...state.allIds],
            };
            for (let user of action.states) {
                state.states[user.user] = {...user.state};
                if (state.allIds.indexOf(user.user) === -1) {
                    state.allIds.push(user.user);
                }
            }
            break;
    }
    return state;
};

export default reducer
