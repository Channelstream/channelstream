'use strict';

export const types = {
    SET_PAGE: 'app/SET_PAGE'
};

export const actions = {
    setPage: (page) => ({
        type: types.SET_PAGE,
        page: page
    })
};

const INITIAL_STATE = {
    selectedPage: 'chat'
};

export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET_PAGE:
            state = {...state, selectedPage: action.page};
            break;
    }
    return state;
};

export default reducer
