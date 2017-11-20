'use strict';

export const types = {
    SET: 'serverStats/SET'
};

export const actions = {
    set: (stats) => ({
        type: types.SET,
        stats: stats
    })
};

const INITIAL_STATE = {
    uptime: undefined,
    remembered_user_count: 0,
    unique_user_count: 0,
    total_connections: 0,
    total_channels: 0,
    total_unique_messages: 0,
    total_messages: 0
};

export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET:
            state = {...action.stats};
            break;
    }
    return state;
};

export default reducer
