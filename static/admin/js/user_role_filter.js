'use strict';
(function () {
    const TEAM_ROLES = {
        '':          ['admin'],
        'team_9':    ['lead', 'member'],
        'cs':        ['lead', 'member'],
        'market':    ['lead', 'primary', 'rolling', 'loading_dock'],
        'corporate': ['lead', 'member'],
    };

    function filterRoles() {
        const teamSel = document.getElementById('id_team');
        const roleSel = document.getElementById('id_role');
        if (!teamSel || !roleSel) return;

        const team = teamSel.value || '';
        const allowed = TEAM_ROLES[team] || Object.values(TEAM_ROLES).flat();

        Array.from(roleSel.options).forEach(opt => {
            opt.hidden = !allowed.includes(opt.value);
        });

        if (!allowed.includes(roleSel.value)) {
            roleSel.value = allowed[0];
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        const teamSel = document.getElementById('id_team');
        if (teamSel) {
            teamSel.addEventListener('change', filterRoles);
            filterRoles();
        }
    });
})();
