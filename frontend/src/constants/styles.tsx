import {
    Business as BusinessIcon,
    Computer as TechIcon,
    LocalCafe as LifeIcon,
    School as EduIcon,
    TheaterComedy as FunIcon,
    Store as CommercialIcon,
    Palette as ArtIcon,
    PhotoCamera as DocIcon,
    Weekend as RelaxIcon,
    Gavel as SeriousIcon,
} from '@mui/icons-material';

export interface StyleConfig {
    IconComponent: React.ComponentType;
    gradient: string;
    color: string;
}

export const STYLE_CONFIG: Record<string, StyleConfig> = {
    '专业': {
        IconComponent: BusinessIcon,
        gradient: 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)',
        color: '#3498db'
    },
    '科技': {
        IconComponent: TechIcon,
        gradient: 'linear-gradient(135deg, #000428 0%, #004e92 100%)',
        color: '#004e92'
    },
    '生活': {
        IconComponent: LifeIcon,
        gradient: 'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)',
        color: '#56ab2f'
    },
    '教育': {
        IconComponent: EduIcon,
        gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        color: '#4facfe'
    },
    '娱乐': {
        IconComponent: FunIcon,
        gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        color: '#fa709a'
    },
    '商业': {
        IconComponent: CommercialIcon,
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: '#667eea'
    },
    '艺术': {
        IconComponent: ArtIcon,
        gradient: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)',
        color: '#ff9a9e'
    },
    '纪录片': {
        IconComponent: DocIcon,
        gradient: 'linear-gradient(135deg, #434343 0%, #000000 100%)',
        color: '#888'
    },
    '轻松': {
        IconComponent: RelaxIcon,
        gradient: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
        color: '#66a6ff'
    },
    '严肃': {
        IconComponent: SeriousIcon,
        gradient: 'linear-gradient(135deg, #20002c 0%, #cbb4d4 100%)',
        color: '#8e44ad'
    },
};

export const DEFAULT_STYLE = '专业';
export const DEFAULT_TARGET_DURATION = 60;
export const DEFAULT_SHOT_COUNT = 6;
