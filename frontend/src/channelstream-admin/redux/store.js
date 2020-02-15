import { init } from '@rematch/core'
import logger from 'redux-logger/dist/redux-logger';

import * as models from './models'

const store = init({
    models,
});

export {store};
