import React from 'react';
import { Box, Paper, Typography, Tooltip, useTheme, alpha } from '@mui/material';
import { motion } from 'framer-motion';
import { MovieCreation as MovieIcon } from '@mui/icons-material';
import { STYLE_CONFIG } from '../../constants/styles';

interface StyleCardProps {
    name: string;
    active: boolean;
    onClick: () => void;
}

const StyleCard: React.FC<StyleCardProps> = ({ name, active, onClick }) => {
    const theme = useTheme();
    const config = STYLE_CONFIG[name] || {
        IconComponent: MovieIcon,
        gradient: 'grey',
        color: 'grey'
    };
    const IconComponent = config.IconComponent;

    return (
        <Tooltip title={name}>
            <Paper
                component={motion.div}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onClick}
                sx={{
                    width: '100%',
                    aspectRatio: '1',
                    cursor: 'pointer',
                    background: active ? config.gradient : alpha(theme.palette.background.paper, 0.2),
                    border: `1px solid ${active ? 'transparent' : alpha(theme.palette.common.white, 0.1)}`,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    position: 'relative',
                    transition: 'all 0.2s',
                    boxShadow: active ? `0 0 15px ${alpha(config.color, 0.5)}` : 'none',
                }}
            >
                <Box sx={{ fontSize: '1.5rem' }}><IconComponent /></Box>
                {active && (
                    <Box sx={{
                        position: 'absolute',
                        bottom: -20,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        whiteSpace: 'nowrap'
                    }}>
                        <Typography variant="caption" sx={{
                            fontSize: '0.7rem',
                            color: config.color,
                            fontWeight: 'bold'
                        }}>
                            {name}
                        </Typography>
                    </Box>
                )}
            </Paper>
        </Tooltip>
    );
};

export default StyleCard;
