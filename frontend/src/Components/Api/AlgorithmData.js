import { serverUrl } from "./Server";
import axios from "axios";

/*****  data of Load Control algorithm  *****/
let loadControlPromise = axios.get(`${serverUrl}/algorithm/load_controller/`);
export { loadControlPromise };

/*****  data of Load Forecast algorithm  *****/
let loadForecastPromise = axios.get(`${serverUrl}/algorithm/load_forecast/`);
const fieldsLoadForecast = [
    "residential_l1_load",
    "residential_l2_load",
    "residential_mud_load",
    "work_load",
    "fast_load",
    "public_l2_load",
    "total_load",
];
export { loadForecastPromise, fieldsLoadForecast };
