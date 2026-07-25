import pytest
import database
from server import app


@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "test_server_data.db"
    database.DB_PATH = str(db_file)
    database.init_db()
    
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"JustSay" in rv.data


def test_complete_onboarding_route(client):
    rv = client.post('/complete_onboarding', data={
        'speaking_style': 'Formal',
        'hotkey_ptt': 'ctrl+windows',
        'hotkey_toggle': 'ctrl+windows+space'
    }, follow_redirects=True)
    assert rv.status_code == 200
    
    settings = database.get_user_settings("localuser@localhost")
    assert settings['speaking_style'] == 'Formal'
    assert settings['onboarded'] is True


def test_dictionary_routes(client):
    rv = client.post('/add_to_dictionary', data={'word': 'Antigravity'}, follow_redirects=True)
    assert rv.status_code == 200
    assert "Antigravity" in database.get_dictionary()

    rv = client.get('/delete_from_dictionary/Antigravity', follow_redirects=True)
    assert rv.status_code == 200
    assert "Antigravity" not in database.get_dictionary()


def test_set_theme_api(client):
    rv = client.post('/api/set_theme', json={'theme': 'dark'})
    assert rv.status_code == 200
    assert rv.get_json() == {"ok": True}
    
    settings = database.get_user_settings("localuser@localhost")
    assert settings['theme'] == 'dark'


def test_prompts_routes(client):
    rv = client.post('/add_prompt', data={'prompt_text': 'Test Prompt'}, follow_redirects=True)
    assert rv.status_code == 200
    
    prompts = database.get_all_prompts()
    test_p = [p for p in prompts if p['prompt_text'] == 'Test Prompt']
    assert len(test_p) == 1
    
    prompt_id = test_p[0]['id']
    rv = client.get(f'/set_active/{prompt_id}', follow_redirects=True)
    assert rv.status_code == 200
    assert database.get_active_prompt() == 'Test Prompt'
    
    rv = client.get(f'/delete_prompt/{prompt_id}', follow_redirects=True)
    assert rv.status_code == 200
    prompts_after = database.get_all_prompts()
    assert not any(p['id'] == prompt_id for p in prompts_after)
