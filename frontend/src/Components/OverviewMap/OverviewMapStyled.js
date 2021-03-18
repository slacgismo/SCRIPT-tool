import styled from "styled-components";
import { rgba } from "polished";

const BORDER_STYLE = `0.2rem solid ${rgba("#000", 0.15)}`;
const STROKE_COLOR = "#fff";
const BASIC_COLOR = [5, 97, 0];
const COLOR_PERCENTAGE_ESP = 0.2;

export const Wrapper = styled.div`
    display: flex;
    flex-flow: nowrap row;
    @media (max-width: 600px) {
        flex-flow: nowrap column;
    }
`;

export const Output = styled.div`
    margin: 1rem;
    padding: 1rem;
    flex: 1 1 0;
    border: ${BORDER_STYLE};
    @media (max-width: 600px) {
        padding-right: 0;
        padding-bottom: 1rem;
        border-right: none;
        border-bottom: 0.2rem solid ${BORDER_STYLE};
    }
`;

export const MapWrapper = styled.div`
    padding-left: 1rem;
    flex: 1 1 auto;
    @media (max-width: 600px) {
        padding-left: 0;
        padding-top: 1rem;
    }
    svg {
        stroke: ${STROKE_COLOR};
        stroke-width: 0.1;
        stroke-linecap: round;
        stroke-linejoin: round;
        path {
            :focus {
                outline: 0;
            }
        }
    }
`;

export const Tooltip = styled.div`
    position: fixed;
    padding: 0.25rem;
    background: white;
    border: 0.2rem solid #ccc;
`;

export const ParamTabs = styled.div`
    position: absolute;
    left: 2rem;
    top: 0.5rem;
    h2 {
        position: relative;
        left: 0.5rem;
        color: #575757;
        font-size: 1.7rem;
    }
    button {
        display: block;
        font-size: 1rem;
        color: #575757;
    }
    button.chosen {
        font-weight: bold;
    }
`;

export const LegendWrapper = styled.div`
    position: absolute;
    right: 2rem;
    top: 0.5rem;
    padding: 1.5rem;
`;

export const getStyledMapWrapperByCountyColors = (countyColors) => {
    let countyColorsCSS = "";
    Object.keys(countyColors).forEach((county) => {
        countyColorsCSS += `
      path[name='${county}'] {
        fill: ${countyColors[county]["color"]};
      }
    `;
    });

    const StyledMap = styled(MapWrapper)`
        position: relative;
        padding: 0;

        svg#usa-ca {
            background-color: #bdbdbd;
            margin: 0;
            padding: 2rem;
            width: 100%;
            height: 85vh;
            viewbox: "500px 500px 500px 500px";
            path {
                cursor: pointer;
                &:hover {
                    opacity: 0.75;
                }
            }
            ${countyColorsCSS}
        }
    `;

    return StyledMap;
};

/**
 * Add color attribute by an existing attribute(e.g. totalEnergy).
 *
 * The result is caused by side effect.
 *
 *  {
 *    "santa clara": {
 *      "totalEnergy": 12
 *    },
 *    ...
 *  }
 *
 *  ||
 *  \/
 *
 *  {
 *    "santa clara": {
 *      "totalEnergy": 12,
 *      "color": "#aaaaaa",
 *    },
 *    ...
 *  }
 *
 */
export const addCountyColorByAttr = (counties, attrName) => {
    let attrOfCounties = getValuesOfAttr(counties, attrName);

    const countyNames = Object.keys(counties);
    const attrPercentageOfCounties = numbers2percentages(attrOfCounties);

    countyNames.forEach((countyName, i) => {
        counties[countyName].color = rgba(
            ...BASIC_COLOR,
            attrPercentageOfCounties[i]
        );
    });
};

export const getExtremeValuesOfAttr = (counties, attrName) => {
    let attrOfCounties = getValuesOfAttr(counties, attrName);
    return {
        maxValue: Math.max(...attrOfCounties),
        minValue: Math.min(...attrOfCounties),
    };
};

export const getBasicColor = () => {
    return BASIC_COLOR;
};

export const getColorPercentageEsp = () => {
    return COLOR_PERCENTAGE_ESP;
};

const getValuesOfAttr = (counties, attrName) => {
    const countyNames = Object.keys(counties);
    let attrOfCounties = [];
    countyNames.forEach((countyName) => {
        attrOfCounties.push(counties[countyName][attrName]);
    });
    return attrOfCounties;
};

const numbers2percentages = (nums) => {
    if (Math.max(...nums) === Math.min(...nums)) {
        return nums.map((num) => 0.5);
    }

    const maxNum = Math.max(...nums);
    const minNum =
        Math.min(...nums) -
        (Math.max(...nums) - Math.min(...nums)) * COLOR_PERCENTAGE_ESP;
    return nums.map((num) => (num - minNum) / (maxNum - minNum));
};
