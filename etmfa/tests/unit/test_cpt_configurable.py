import pytest
from etmfa.server.config import Config


@pytest.mark.parametrize(
    "aidoc_id, link_level, toc, link_id, section_text, user_id, protocol, config_variables, status_code, comments", [
        ('94770170-19c2-4a3e-9505-7e6b9c683b3d', '1', '', 'b35b238a-89d3-11ed-a6e8-005056ab6469', '',
         'Dig2_Batch_Tester',
         'cicl.06ed2096-0749-4ead-a892-9e57ead4fcbc',
         'clinical_terms,time_points,preferred_terms,redaction_attributes,references,properties', 200,
         "provide all data for get section "),
        ('94770170-19c2-4a3e-9505-7e6b9c683b3d', '1', '1', 'b35b238a-89d3-11ed-a6e8-005056ab6469', '',
         'Dig2_Batch_Tester',
         'cicl.06ed2096-0749-4ead-a892-9e57ead4fcbc',
         'clinical_terms,time_points,preferred_terms,redaction_attributes,references,properties', 200,
         "provide all data with toc 1"),
        ('94770170-19c2-4a3e-9505-7e6b9c683b3d', '1', '3', 'b35b238a-89d3-11ed-a6e8-005056ab6469', '',
         'Dig2_Batch_Tester',
         'cicl.06ed2096-0749-4ead-a892-9e57ead4fcbc',
         'clinical_terms,time_points,preferred_terms,redaction_attributes,references,properties', 200,
         "provide all data with toc 3"),
        ('272c5cab-fbf3-44f8-8afe-not-exists', '', '', 'b35b238a-89d3-11ed-a6e8-005056ab6469', '',
         'Dig2_Batch_Tester',
         'protocol',
         'clinical_terms,time_points,preferred_terms,redaction_attributes,references,properties', 400,
         "No link level and doc id id does not exists"),
        ('a', '1', '1', '', '',
         'Dig2_Batch_Tester', '', '', 500, "provided invalid data"),
        ('94770170-19c2-4a3e-9505-7e6b9c683b3d', '1', '', '', '3.2. Safety',
         'Dig2_Batch_Tester',
         'cicl.06ed2096-0749-4ead-a892-9e57ead4fcbc',
         'clinical_terms,time_points,preferred_terms,redaction_attributes,references,properties', 200,
         "from section text response verifying"),
    ])
def test_configurable_parameter(new_app_context, aidoc_id, link_level, toc, link_id, section_text, user_id, protocol,
                                config_variables, status_code, comments):
    """
        Tests document with configurable parameters data for document with doc_id, protocol, user_id, link_level and link_id and toc.
    """
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        get_config_response = client.get("/pd/api/cpt_data/get_section_data_configurable_parameter",
                                         json={"aidoc_id": aidoc_id,
                                               "link_level": link_level,
                                               "link_id": link_id,
                                               "user_id": user_id,
                                               "protocol": protocol,
                                               "toc": toc,
                                               "section_text": section_text,
                                               "config_variables": config_variables
                                               },
                                         headers=Config.UNIT_TEST_HEADERS)

        assert get_config_response.status_code == status_code
